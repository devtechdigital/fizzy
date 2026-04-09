# cli-anything-fizzy

CLI harness for Fizzy Kanban Board (https://tasks.baum.to).

## Installation

```bash
cd /Volumes/2TB/Baum\ Products/fizzy/agent-harness
pip install -e .
```

## Configuration

```bash
# Interactive setup
cli-anything-fizzy auth setup

# Or use environment variables
export FIZZY_ACCESS_TOKEN="your-bearer-token"
export FIZZY_BASE_URL="https://tasks.baum.to"
```

Config is stored at `~/.config/cli-anything-fizzy/config.json`.

## Usage

### REPL Mode (default)

```bash
cli-anything-fizzy
```

### Command Mode

```bash
# Boards
cli-anything-fizzy boards list
cli-anything-fizzy boards show <board-id>
cli-anything-fizzy boards create "My Board"

# Cards
cli-anything-fizzy cards show <number>
cli-anything-fizzy cards create <board-id> "Card title"
cli-anything-fizzy cards close <number>
cli-anything-fizzy cards reopen <number>
cli-anything-fizzy cards move <number> <column-id>

# Columns
cli-anything-fizzy columns list <board-id>
cli-anything-fizzy columns create <board-id> "Column Name"

# Comments
cli-anything-fizzy comments list <card-number>
cli-anything-fizzy comments add <card-number> "Comment body"

# Tags & Users
cli-anything-fizzy tags list
cli-anything-fizzy users list
cli-anything-fizzy users show <user-id>
```

### JSON Output

Add `--json` before the subcommand for raw JSON:

```bash
cli-anything-fizzy --json boards list
```

## Testing

```bash
# Unit tests (no network required)
pytest cli_anything/fizzy/tests/test_core.py -v

# E2E tests (requires live instance)
FIZZY_ACCESS_TOKEN=xxx FIZZY_BASE_URL=https://tasks.baum.to pytest cli_anything/fizzy/tests/test_full_e2e.py -v
```
