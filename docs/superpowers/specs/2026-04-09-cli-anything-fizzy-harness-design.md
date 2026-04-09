# CLI-Anything Fizzy Harness — Design Spec

> Date: 2026-04-09
> Status: Approved
> Author: Kevin Baum + Oakie

## Summary

Install CLI-Anything as a shared tool in the Baum workspace and use it to generate a CLI harness for Fizzy (our Kanban board at tasks.baum.to). The harness gives humans and AI agents programmatic read/write access to Fizzy via the command line. Long-term vision: AI agents become first-class Fizzy users — assigned cards, updating status, closing work.

## Context

- **Fizzy** is deployed on mini1 as a Docker container (port 3006), accessible at `https://tasks.baum.to` via Cloudflare Tunnel.
- **CLI-Anything** is an open-source framework (HKUDS/CLI-Anything) that auto-generates CLI harnesses for software applications, making them agent-accessible. We already have a working harness for Draw.io at `/Volumes/2TB/drawio-desktop/agent-harness`.
- Fizzy has no existing API. It's a Rails web app with Hotwire frontend, SQLite database, and existing infrastructure for access tokens and webhooks.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Approach | Let CLI-Anything analyse and generate, then bridge to mini1 | Respects the framework's analysis. Avoids premature API decisions. |
| CLI-Anything location | `~/Baum/tools/cli-anything/` | Shared tool, consistent with GOTCHA framework |
| Harness location | `/Volumes/2TB/Baum Products/fizzy/agent-harness/` | Co-located with source, matches Draw.io pattern |
| Fizzy operations scope | Full parity (staged) | Phase 1: core CRUD. Expand through phases. |
| Connection strategy | Evaluate post-generation | CLI-Anything may choose Rails console, HTTP, or suggest an API. We adapt. |

## Architecture

### Workspace Layout

```
~/Baum/tools/cli-anything/          # CLI-Anything framework (shared tool)
/Volumes/2TB/Baum Products/fizzy/
  ├── agent-harness/                # Generated Fizzy CLI harness
  │   ├── cli_anything/fizzy/       # Click-based CLI source
  │   ├── setup.py                  # pip-installable
  │   ├── FIZZY.md                  # SKILL.md for agent discovery
  │   └── tests/                    # Generated test suite
  └── ...                           # Fizzy source code
```

### Connection Layer

Post-generation, the harness gets a connection layer to reach the Fizzy instance on mini1:

- **Rails console mode**: Commands wrapped in `ssh mini1 "docker exec fizzy bin/rails runner '...'"`. Works from any machine that can SSH to mini1.
- **HTTP mode**: Commands target `https://tasks.baum.to` with access token auth. Requires API endpoints in the Fizzy fork (Phase 2).
- **Direct DB mode**: SSH tunnel to SQLite. Least preferred — bypasses app logic.

Configuration stored in `~/.config/cli-anything-fizzy/config.json`:

```json
{
  "host": "mini1",
  "mode": "rails-console",
  "auth": {
    "type": "ssh-key"
  }
}
```

Mode and config determined after evaluating CLI-Anything's generated output.

### Expected CLI Interface

```bash
# Human-readable
cli-anything-fizzy boards list
cli-anything-fizzy cards create --board "Sprint 1" --title "Fix login bug" --column "To Do"
cli-anything-fizzy cards move <card-id> --column "In Progress"
cli-anything-fizzy cards comment <card-id> "Started work on this"

# Machine-readable (for agents)
cli-anything-fizzy --json boards list
cli-anything-fizzy --json cards show <card-id>

# Interactive REPL
cli-anything-fizzy
```

## Phased Roadmap

### Phase 1 — Generate & Connect (this implementation cycle)

- Clone CLI-Anything to `~/Baum/tools/cli-anything/`
- Run the 7-phase pipeline against the Fizzy source at `/Volumes/2TB/Baum Products/fizzy/`, outputting to `agent-harness/`
- Evaluate output, add connection layer to mini1
- Install harness as `cli-anything-fizzy` on system PATH
- Verify core operations: list boards, read/create/move cards, list columns
- SKILL.md published for agent discovery

### Phase 2 — API & Network Access (next cycle, if needed)

- Based on Phase 1 learnings, build a lightweight JSON API in the Fizzy fork
- Token auth via Fizzy's existing AccessToken model
- Harness switches to HTTP mode, works from any machine via `tasks.baum.to`
- Regenerate/update harness to target API endpoints

### Phase 3 — Agentic Layer (future)

- Create agent users in Fizzy — named identities mapping to Baum agent team (e.g. "Builder Agent", "Growth Agent")
- Agents authenticate via access tokens, interact through CLI
- Workflow patterns: agent picks up card → moves to "in progress" → adds status comments → moves to "done"
- Board-per-project conventions for agent discovery
- Integration with Baum orchestration layer — work assigned in Fizzy, agents execute via CLI

## Out of Scope

- Modifying Fizzy's web UI
- Multi-tenant mode
- SMTP/email configuration (already complete)
- Custom Fizzy features beyond what the CLI exposes
- Phase 2 and 3 implementation (separate specs when the time comes)

## Dependencies

- Python 3.10+ (available on M3 Mac)
- Click 8.0+ (installed with CLI-Anything)
- SSH access to mini1 (confirmed working)
- Fizzy source clone at `/Volumes/2TB/Baum Products/fizzy/`
- Running Fizzy instance on mini1 (confirmed at tasks.baum.to)

## Risks

| Risk | Mitigation |
|---|---|
| CLI-Anything can't analyse a Rails web app as well as a desktop app | We have the full source code locally. If generation is incomplete, we manually extend the harness. |
| Rails console bridge is slow for agent workflows | Phase 2 API replaces it with HTTP calls. |
| Fizzy schema changes on upstream updates | Harness is co-located with source — regenerate when pulling upstream. |
| Phase 1 CLI only works from machines with SSH to mini1 | Acceptable constraint. Phase 2 solves with HTTP. |
