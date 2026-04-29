# Fizzy

This file provides guidance to AI coding agents working with this repository.

## What is Fizzy?

Fizzy is a collaborative project management and issue tracking application built by 37signals/Basecamp. It's a kanban-style tool for teams to create and manage cards (tasks/issues) across boards, organize work into columns representing workflow stages, and collaborate via comments, mentions, and assignments.

## Fork-specific notes (read first)

This is `devtechdigital/fizzy`, a fork of `basecamp/fizzy`. Key things to know:

- **Runtime is on `mini1`, not this Mac.** The live `tasks.baum.to` instance runs as a Docker container on mini1 (`extmini-01`, 192.168.20.27), Colima-managed, port 3006 → container :80, with data in the `fizzy-data` Docker volume. This local clone is for **editing code only**. Running `bin/dev` here spins up an isolated dev instance with no relation to production.
- **Deploy is custom (not Kamal).** Despite `config/deploy*.yml` shipping kamal targets, this fork deploys via a manual `git push origin main` → SSH into mini1 → `docker build` → cutover. See the `mini1 cloudflared tunnel inventory + restart procedure` and `Fizzy deploy workflow` memories in the **`fizzy` Muninn vault** for the full procedure (keychain unlock, env capture, fizzy_old rollback dance, etc.).
- **Cloudflared tunnel runs on mini1**, not here. tasks.baum.to → `https://tasks.baum.to` → cloudflared on mini1 → `localhost:3006` (the container). Tunnel is a system LaunchDaemon (`/Library/LaunchDaemons/com.kevin.cloudflared-fizzy-tasks.plist`) — autostarts on boot, no GUI login required. Same arrangement for `vault.baum.to` (vaultwarden) and `filament.qrs.ing` (filament-home), all on mini1.
- **Upstream cadence.** Track `basecamp/fizzy` `main`. Don't bump `.ruby-version` ahead of upstream — divergence creates merge friction every sync. Upstream pin is the source of truth; the Dockerfile reads `ARG RUBY_VERSION` from `.ruby-version` and Docker on mini1 will install whatever it points to.
- **When debugging tasks.baum.to outages, debug mini1 first** — not this Mac. Containers usually stay healthy; the common failure mode is the cloudflared LaunchDaemon dying, leaving 530 (origin unreachable) or 1033 (tunnel disconnected).

For the full operating context — what runs where, how to deploy, restart procedures, MySQL/SQLite reality, env vars, prior incidents — search the `fizzy` Muninn vault: `mcp__muninn__muninn_recall(vault="fizzy", context=[...])`. The `default` vault has minimal Fizzy info and led to a multi-hour wrong-machine debug once. Don't repeat that.

## Development Commands

### Setup and Server
```bash
bin/setup              # Initial setup (installs gems, creates DB, loads schema)
bin/dev                # Start development server (runs on port 3006)
```

Development URL: http://app.fizzy.localhost:3006
Login with: david@example.com (development fixtures), password will appear in the browser console

### Testing
```bash
bin/rails test                    # Run unit tests (fast)
bin/rails test test/path/file_test.rb  # Run single test file
bin/rails test:system             # Run system tests (Capybara + Selenium)
bin/ci                            # Run full CI suite (style, security, tests)

# For parallel test execution issues, use:
PARALLEL_WORKERS=1 bin/rails test
```

CI pipeline (`bin/ci`) runs:
1. Rubocop (style)
2. Bundler audit (gem security)
3. Importmap audit
4. Brakeman (security scan)
5. Application tests
6. System tests

### Database
```bash
bin/rails db:fixtures:load   # Load fixture data
bin/rails db:migrate          # Run migrations
bin/rails db:reset            # Drop, create, and load schema
```

### Other Utilities
```bash
bin/rails dev:email          # Toggle letter_opener for email preview
bin/jobs                     # Manage Solid Queue jobs
bin/kamal deploy             # Deploy (requires 1Password CLI for secrets)
```

## Deploy

Default branch: `main`. Live target: `tasks.baum.to` (Docker container on mini1).

**Quick path** (full details in `fizzy` Muninn vault → memory "Fizzy deploy workflow"):

1. **On this Mac** — `git fetch upstream && git merge upstream/main` (resolve conflicts in cards files), make atomic commits, `git push origin main`.
2. **On mini1** — `ssh -t mini1` and run **one** chained command (keychain must unlock in the same session):
   ```
   security unlock-keychain ~/Library/Keychains/login.keychain-db && \
     cd ~/fizzy-build && git pull && \
     /usr/local/bin/docker build -t fizzy:<tag> . 2>&1 | tee /tmp/fizzy-build.log | tail -40
   ```
3. **Cutover** (~30s downtime, fizzy-data volume preserved):
   ```
   docker inspect fizzy --format '{{range .Config.Env}}{{println .}}{{end}}' > /tmp/fizzy.env
   docker stop fizzy && docker rename fizzy fizzy_old
   docker run -d --name fizzy --env-file /tmp/fizzy.env -p 3006:80 \
     -v fizzy-data:/rails/storage --restart unless-stopped fizzy:<tag>
   ```
4. **Rollback** if anything's wrong: `docker stop fizzy && docker rm fizzy && docker rename fizzy_old fizzy && docker start fizzy`.
5. After 24–48h of confidence: `docker rm fizzy_old`.

**Upstream's kamal deploy** (`bin/kamal deploy -d production|beta1-4`) is configured in `config/deploy*.yml` but **not used by this fork**. Ignore unless you're cutting a parallel hosted deployment.

## Architecture Overview

### Multi-Tenancy (URL-Based)

Fizzy uses **URL path-based multi-tenancy**:
- Each Account (tenant) has a unique `external_account_id` (7+ digits)
- URLs are prefixed: `/{account_id}/boards/...`
- Middleware (`AccountSlug::Extractor`) extracts the account ID from the URL and sets `Current.account`
- The slug is moved from `PATH_INFO` to `SCRIPT_NAME`, making Rails think it's "mounted" at that path
- All models include `account_id` for data isolation
- Background jobs automatically serialize and restore account context

**Key insight**: This architecture allows multi-tenancy without subdomains or separate databases, making local development and testing simpler.

### Authentication & Authorization

**Passwordless magic link authentication**:
- Global `Identity` (email-based) can have `Users` in multiple Accounts
- Users belong to an Account and have roles: owner, admin, member, system
- Sessions managed via signed cookies
- Board-level access control via `Access` records

### Core Domain Models

**Account** → The tenant/organization
- Has users, boards, cards, tags, webhooks
- Has entropy configuration for auto-postponement

**Identity** → Global user (email)
- Can have Users in multiple Accounts
- Session management tied to Identity

**User** → Account membership
- Belongs to Account and Identity
- Has role (owner/admin/member/system)
- Board access via explicit `Access` records

**Board** → Primary organizational unit
- Has columns for workflow stages
- Can be "all access" or selective
- Can be published publicly with shareable key

**Card** → Main work item (task/issue)
- Sequential number within each Account
- Rich text description and attachments
- Lifecycle: triage → columns → closed/not_now
- Automatically postpones after inactivity ("entropy")

**Event** → Records all significant actions
- Polymorphic association to changed object
- Drives activity timeline, notifications, webhooks
- Has JSON `particulars` for action-specific data

### Entropy System

Cards automatically "postpone" (move to "not now") after inactivity:
- Account-level default entropy period
- Board-level entropy override
- Prevents endless todo lists from accumulating
- Configurable via Account/Board settings

### UUID Primary Keys

All tables use UUIDs (UUIDv7 format, base36-encoded as 25-char strings):
- Custom fixture UUID generation maintains deterministic ordering for tests
- Fixtures are always "older" than runtime records
- `.first`/`.last` work correctly in tests

### Background Jobs (Solid Queue)

Database-backed job queue (no Redis):
- Custom `FizzyActiveJobExtensions` prepended to ActiveJob
- Jobs automatically capture/restore `Current.account`
- Mission Control::Jobs for monitoring

Key recurring tasks (via `config/recurring.yml`):
- Deliver bundled notifications (every 30 min)
- Auto-postpone stale cards (hourly)
- Cleanup jobs for expired links, deliveries

### Sharded Full-Text Search

16-shard MySQL full-text search instead of Elasticsearch:
- Shards determined by account ID hash (CRC32)
- Search records denormalized for performance
- Models in `app/models/search/`

### Imports and exports

Allow people to move between OSS and SAAS Fizzy instances:
- Exports/Imports can be written to/read from local or S3 storage depending on the config of the instance (both must be supported)
- Must be able to handle very large ZIP files (500+GB)
- Models in `app/models/account/data_transfer/`, `app/models/zip_file`

## Tools

### Chrome MCP (Local Dev)

URL: `http://app.fizzy.localhost:3006`
Login: david@example.com (passwordless magic link auth - check rails console for link)

Use Chrome MCP tools to interact with the running dev app for UI testing and debugging.

## Coding style

@STYLE.md
