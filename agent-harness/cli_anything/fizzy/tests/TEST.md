# Test Plan: cli-anything-fizzy

## Test Inventory

### Unit Tests (test_core.py) — No network required

| # | Area | Test | What it verifies |
|---|------|------|------------------|
| 1 | Config | test_default_config | Default values are correct |
| 2 | Config | test_load_config_missing_file | Returns defaults when no file |
| 3 | Config | test_save_and_load_config | Round-trip save/load |
| 4 | Config | test_get_config_no_token | Raises RuntimeError |
| 5 | Config | test_get_config_with_env | Env vars override file config |
| 6 | Client | test_client_get | GET request with auth headers |
| 7 | Client | test_client_post | POST request with JSON body |
| 8 | Client | test_client_patch | PATCH request with JSON body |
| 9 | Client | test_client_delete | DELETE request |
| 10 | Client | test_client_401 | Raises FizzyAPIError on 401 |
| 11 | Client | test_client_403 | Raises FizzyAPIError on 403 |
| 12 | Client | test_client_404 | Raises FizzyAPIError on 404 |
| 13 | Client | test_client_422 | Raises FizzyAPIError on 422 |
| 14 | Client | test_client_500 | Raises FizzyAPIError on 500 |
| 15 | Boards | test_list_boards | Calls GET /boards |
| 16 | Boards | test_get_board | Calls GET /boards/:id |
| 17 | Boards | test_create_board | Calls POST /boards |
| 18 | Boards | test_delete_board | Calls DELETE /boards/:id |
| 19 | Cards | test_create_card | Calls POST /boards/:id/cards |
| 20 | Cards | test_get_card | Calls GET /cards/:number |
| 21 | Cards | test_close_card | Calls POST /cards/:number/closure |
| 22 | Cards | test_reopen_card | Calls DELETE /cards/:number/closure |
| 23 | Cards | test_move_card | Calls PATCH /cards/:number/column |
| 24 | Cards | test_assign_user | Calls POST /cards/:n/assignments |
| 25 | Columns | test_list_columns | Calls GET /boards/:id/columns |
| 26 | Columns | test_create_column | Calls POST /boards/:id/columns |
| 27 | Comments | test_list_comments | Calls GET /cards/:n/comments |
| 28 | Comments | test_create_comment | Calls POST /cards/:n/comments |
| 29 | Tags | test_list_tags | Calls GET /tags |
| 30 | Users | test_list_users | Calls GET /users |
| 31 | Users | test_get_user | Calls GET /users/:id |
| 32 | Formatters | test_format_boards | Renders board table |
| 33 | Formatters | test_format_card | Renders card detail view |
| 34 | Formatters | test_format_cards_empty | Handles empty list |
| 35 | Formatters | test_format_comments | Renders comment list |
| 36 | Formatters | test_output_json | JSON mode outputs json.dumps |

### E2E Tests (test_full_e2e.py) — Requires live instance

| # | Test | What it verifies |
|---|------|------------------|
| 1 | test_help | --help flag works |
| 2 | test_version | --version flag works |
| 3 | test_auth_whoami | auth whoami returns user |
| 4 | test_boards_list | boards list returns data |
| 5 | test_boards_list_json | boards list --json returns valid JSON |
| 6 | test_tags_list | tags list works |
| 7 | test_users_list | users list works |
| 8 | test_card_lifecycle | Create, show, close, reopen, delete cycle |
| 9 | test_columns_list | columns list for a board |
| 10 | test_comments_lifecycle | Add and list comments |

## Running Tests

```bash
# Unit tests only
pytest cli_anything/fizzy/tests/test_core.py -v

# E2E tests (skip if no env vars)
FIZZY_ACCESS_TOKEN=xxx pytest cli_anything/fizzy/tests/test_full_e2e.py -v

# All tests with coverage
pytest cli_anything/fizzy/tests/ -v --cov=cli_anything.fizzy
```
