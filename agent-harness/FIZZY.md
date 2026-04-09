# Fizzy — CLI Harness Analysis & SOP

## Software Overview

**Fizzy** is an open-source Kanban board application by 37signals (Basecamp). It manages boards, cards, columns, comments, tags, assignments, and webhooks. Built with Ruby on Rails, Hotwire, and SQLite.

**Instance**: `https://tasks.baum.to` (Docker on mini1, Cloudflare Tunnel)

## Architecture

### Data Model

Fizzy uses a multi-tenant architecture with UUID primary keys:

- **Account**: Top-level tenant container
- **Board**: Kanban board with columns, cards, webhooks
- **Card**: Core work item with status (drafted/triaged/accepted/started/postponed/closed), rich text description, image attachment, 24 behavioral concerns
- **Column**: Board lane with name, color, position
- **Comment**: Card discussion with rich text body and reactions
- **Tag**: Board-level categorization (lowercase, no leading #)
- **Assignment**: Card-to-user assignment (100 limit per card)
- **User**: Account member with role (member/admin/owner)
- **Event**: Activity tracking with polymorphic eventable
- **Webhook**: Outbound event notifications (11 event types)
- **Notification**: User-targeted alerts with read/unread tracking
- **Export**: Background ZIP export with 24-hour retention
- **Filter**: Saved card query with complex filtering

### Authentication

Fizzy supports three auth methods. **Access Tokens** are the CLI mechanism:

- Model: `Identity::AccessToken`
- Header: `Authorization: Bearer <token>`
- Permissions: `read` (GET/HEAD only) or `write` (all methods)
- Create via web UI at `/my/access_tokens`
- Validated via `Identity.find_by_permissable_access_token(token, method:)`

### JSON API

Fizzy has existing Jbuilder JSON views for all core resources:

| Resource | List | Show | Create | Update | Delete |
|----------|------|------|--------|--------|--------|
| Boards | GET /boards | GET /boards/:id | POST /boards | PATCH /boards/:id | DELETE /boards/:id |
| Cards | GET /boards/:id/cards | GET /cards/:number | POST /boards/:id/cards | PATCH /cards/:number | DELETE /cards/:number |
| Columns | GET /boards/:id/columns | — | POST /boards/:id/columns | PATCH /columns/:id | DELETE /columns/:id |
| Comments | GET /cards/:number/comments | GET /cards/:number/comments/:id | POST /cards/:number/comments | PATCH /cards/:number/comments/:id | DELETE /cards/:number/comments/:id |
| Tags | GET /tags | — | — | — | — |
| Users | GET /users | GET /users/:id | — | — | — |
| Assignments | — | — | POST /cards/:number/assignments | — | DELETE /cards/:number/assignments/:id |

All endpoints accept `Accept: application/json` header for JSON responses.

### Card Statuses & Transitions

```
drafted → triaged → accepted → started → closed
                                    ↓
                               postponed → (auto-reopen)
```

Cards can be moved between columns, closed/reopened, and postponed.

## CLI Command Groups

### `auth` — Authentication
- `auth setup` — Configure access token
- `auth test` — Verify token works
- `auth whoami` — Show current user

### `boards` — Board Management
- `boards list` — List all boards
- `boards show <id>` — Show board details with columns
- `boards create --name <name>` — Create a board
- `boards update <id> --name <name>` — Update board
- `boards delete <id>` — Delete board

### `cards` — Card Operations
- `cards list --board <id>` — List cards (filterable by column, status, tag, assignee)
- `cards show <number>` — Show card details
- `cards create --board <id> --title <title>` — Create card
- `cards update <number> --title <title>` — Update card
- `cards close <number>` — Close card
- `cards reopen <number>` — Reopen card
- `cards move <number> --column <id>` — Move card to column
- `cards assign <number> --user <id>` — Assign user to card
- `cards unassign <number> --user <id>` — Remove assignment
- `cards tag <number> --tag <title>` — Add tag to card
- `cards untag <number> --tag <title>` — Remove tag

### `columns` — Column Management
- `columns list --board <id>` — List columns for board
- `columns create --board <id> --name <name>` — Create column
- `columns update <id> --name <name>` — Update column
- `columns delete <id>` — Delete column

### `comments` — Comment Operations
- `comments list --card <number>` — List comments on card
- `comments create --card <number> --body <text>` — Add comment
- `comments update <id> --card <number> --body <text>` — Edit comment
- `comments delete <id> --card <number>` — Delete comment

### `tags` — Tag Management
- `tags list` — List all tags

### `users` — User Management
- `users list` — List all users
- `users show <id>` — Show user details

### `webhooks` — Webhook Management
- `webhooks list --board <id>` — List webhooks for board
- `webhooks create --board <id> --url <url>` — Create webhook
- `webhooks delete <id> --board <id>` — Delete webhook

### `exports` — Data Export
- `exports create` — Trigger data export
- `exports status <id>` — Check export status

## Output Formats

All commands support `--json` flag for machine-readable JSON output.

**Human-readable** (default): Formatted tables and text
**JSON** (`--json`): Structured JSON matching Fizzy's Jbuilder output

## Configuration

Config stored at `~/.config/cli-anything-fizzy/config.json`:

```json
{
  "base_url": "https://tasks.baum.to",
  "access_token": "<bearer-token>"
}
```

## Installation

```bash
cd /Volumes/2TB/Baum\ Products/fizzy/agent-harness
pip install -e .
cli-anything-fizzy auth setup
```

## Dependencies

- Python 3.10+
- click >= 8.0
- requests (HTTP client)
- prompt-toolkit >= 3.0 (REPL)
- Running Fizzy instance with access token
