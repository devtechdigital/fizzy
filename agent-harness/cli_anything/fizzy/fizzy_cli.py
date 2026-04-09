"""Main CLI entry point for cli-anything-fizzy."""

import json
import sys

import click

from cli_anything.fizzy import __version__
from cli_anything.fizzy.core.client import FizzyClient, FizzyAPIError
from cli_anything.fizzy.core import config as cfg
from cli_anything.fizzy.core import boards as boards_mod
from cli_anything.fizzy.core import cards as cards_mod
from cli_anything.fizzy.core import columns as columns_mod
from cli_anything.fizzy.core import comments as comments_mod
from cli_anything.fizzy.core import tags as tags_mod
from cli_anything.fizzy.core import users as users_mod
from cli_anything.fizzy.utils.formatters import (
    format_boards,
    format_board,
    format_card,
    format_cards,
    format_columns,
    format_comments,
    format_tags,
    format_users,
    format_user,
    output,
)


pass_client = click.make_pass_decorator(FizzyClient, ensure=True)


def _get_client(ctx) -> FizzyClient:
    """Get or create a FizzyClient from the context."""
    if "client" not in ctx.obj:
        try:
            conf = cfg.get_config_with_env()
        except RuntimeError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        ctx.obj["client"] = FizzyClient(
            conf["base_url"],
            conf["access_token"],
            account_prefix=conf.get("account_prefix", "/1"),
        )
    return ctx.obj["client"]


def _handle_api_error(e: FizzyAPIError):
    """Print API error and exit."""
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)


# ── Root group ────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
@click.option("--config", "config_path", type=click.Path(), help="Config file path")
@click.version_option(__version__, prog_name="cli-anything-fizzy")
@click.pass_context
def cli(ctx, as_json, config_path):
    """Fizzy Kanban Board CLI — manage boards, cards, columns, and more."""
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    if config_path:
        ctx.obj["config_path"] = config_path

    if ctx.invoked_subcommand is None:
        _run_repl(ctx)


def _run_repl(ctx):
    """Launch the interactive REPL."""
    try:
        from cli_anything.fizzy.utils.repl_skin import ReplSkin
    except ImportError:
        click.echo("REPL requires prompt-toolkit. Install it with: pip install prompt-toolkit")
        sys.exit(1)

    skin = ReplSkin("fizzy", version=__version__)
    skin.print_banner()

    session = skin.create_prompt_session()

    while True:
        try:
            line = skin.get_input(session, context="fizzy")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        if line.lower() in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if line.lower() in ("help", "h", "?"):
            skin.help({
                "auth setup":           "Configure access token",
                "auth whoami":          "Show current user",
                "boards list":          "List all boards",
                "boards show <id>":     "Show board details",
                "boards create <name>": "Create a new board",
                "cards show <number>":  "Show card details",
                "cards create":         "Create a card (interactive)",
                "cards close <number>": "Close a card",
                "cards reopen <number>":"Reopen a card",
                "cards move <n> <col>": "Move card to column",
                "columns list <board>": "List columns for a board",
                "comments list <card#>":"List comments on a card",
                "comments add <card#>": "Add comment (interactive)",
                "tags list":            "List all tags",
                "users list":           "List all users",
                "quit":                 "Exit the REPL",
            })
            continue

        # Parse and dispatch through Click
        args = line.split()
        try:
            cli.main(args=args, standalone_mode=False, **ctx.params)
        except SystemExit:
            pass
        except FizzyAPIError as e:
            skin.error(str(e))
        except Exception as e:
            skin.error(str(e))


# ── Auth commands ─────────────────────────────────────────────────────


@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command("setup")
def auth_setup():
    """Configure Fizzy access token."""
    cfg.setup()
    click.echo("Setup complete.")


@auth.command("whoami")
@click.pass_context
def auth_whoami(ctx):
    """Show current authenticated user."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        users = users_mod.list_users(client)
        if users:
            output(users[0] if isinstance(users, list) else users, format_user, as_json)
        else:
            click.echo("No user information available.")
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── Board commands ────────────────────────────────────────────────────


@cli.group()
def boards():
    """Board management commands."""
    pass


@boards.command("list")
@click.pass_context
def boards_list(ctx):
    """List all boards."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = boards_mod.list_boards(client)
        output(data, format_boards, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@boards.command("show")
@click.argument("board_id")
@click.pass_context
def boards_show(ctx, board_id):
    """Show a board's details."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = boards_mod.get_board(client, board_id)
        output(data, format_board, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@boards.command("create")
@click.argument("name")
@click.pass_context
def boards_create(ctx, name):
    """Create a new board."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = boards_mod.create_board(client, name)
        output(data, format_board, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@boards.command("update")
@click.argument("board_id")
@click.option("--name", required=True, help="New board name")
@click.pass_context
def boards_update(ctx, board_id, name):
    """Update a board."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = boards_mod.update_board(client, board_id, name=name)
        output(data, format_board, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@boards.command("delete")
@click.argument("board_id")
@click.confirmation_option(prompt="Are you sure you want to delete this board?")
@click.pass_context
def boards_delete(ctx, board_id):
    """Delete a board."""
    client = _get_client(ctx)
    try:
        boards_mod.delete_board(client, board_id)
        click.echo("Board deleted.")
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── Card commands ─────────────────────────────────────────────────────


@cli.group()
def cards():
    """Card management commands."""
    pass


@cards.command("show")
@click.argument("card_number")
@click.pass_context
def cards_show(ctx, card_number):
    """Show a card's details."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = cards_mod.get_card(client, card_number)
        output(data, format_card, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("create")
@click.argument("board_id")
@click.argument("title")
@click.option("--column-id", default=None, help="Column ID to place card in")
@click.pass_context
def cards_create(ctx, board_id, title, column_id):
    """Create a new card on a board."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = cards_mod.create_card(client, board_id, title, column_id)
        output(data, format_card, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("update")
@click.argument("card_number")
@click.option("--title", default=None, help="New title")
@click.option("--body", default=None, help="New body text")
@click.pass_context
def cards_update(ctx, card_number, title, body):
    """Update a card."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    kwargs = {}
    if title:
        kwargs["title"] = title
    if body:
        kwargs["body"] = body
    if not kwargs:
        click.echo("Nothing to update. Use --title or --body.", err=True)
        return
    try:
        data = cards_mod.update_card(client, card_number, **kwargs)
        output(data, format_card, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("delete")
@click.argument("card_number")
@click.confirmation_option(prompt="Are you sure you want to delete this card?")
@click.pass_context
def cards_delete(ctx, card_number):
    """Delete a card."""
    client = _get_client(ctx)
    try:
        cards_mod.delete_card(client, card_number)
        click.echo("Card deleted.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("close")
@click.argument("card_number")
@click.pass_context
def cards_close(ctx, card_number):
    """Close a card."""
    client = _get_client(ctx)
    try:
        cards_mod.close_card(client, card_number)
        click.echo(f"Card #{card_number} closed.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("reopen")
@click.argument("card_number")
@click.pass_context
def cards_reopen(ctx, card_number):
    """Reopen a closed card."""
    client = _get_client(ctx)
    try:
        cards_mod.reopen_card(client, card_number)
        click.echo(f"Card #{card_number} reopened.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("move")
@click.argument("card_number")
@click.argument("column_id")
@click.pass_context
def cards_move(ctx, card_number, column_id):
    """Move a card to a different column."""
    client = _get_client(ctx)
    try:
        cards_mod.move_card(client, card_number, column_id)
        click.echo(f"Card #{card_number} moved.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("assign")
@click.argument("card_number")
@click.argument("user_id")
@click.pass_context
def cards_assign(ctx, card_number, user_id):
    """Assign a user to a card."""
    client = _get_client(ctx)
    try:
        cards_mod.assign_user(client, card_number, user_id)
        click.echo(f"User assigned to card #{card_number}.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@cards.command("unassign")
@click.argument("card_number")
@click.argument("assignment_id")
@click.pass_context
def cards_unassign(ctx, card_number, assignment_id):
    """Remove a user assignment from a card."""
    client = _get_client(ctx)
    try:
        cards_mod.unassign_user(client, card_number, assignment_id)
        click.echo(f"Assignment removed from card #{card_number}.")
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── Column commands ───────────────────────────────────────────────────


@cli.group()
def columns():
    """Column management commands."""
    pass


@columns.command("list")
@click.argument("board_id")
@click.pass_context
def columns_list(ctx, board_id):
    """List all columns for a board."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = columns_mod.list_columns(client, board_id)
        output(data, format_columns, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@columns.command("create")
@click.argument("board_id")
@click.argument("name")
@click.pass_context
def columns_create(ctx, board_id, name):
    """Create a new column on a board."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = columns_mod.create_column(client, board_id, name)
        click.echo(json.dumps(data, indent=2) if ctx.obj.get("as_json") else f"Column '{name}' created.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@columns.command("update")
@click.argument("column_id")
@click.option("--name", required=True, help="New column name")
@click.pass_context
def columns_update(ctx, column_id, name):
    """Update a column."""
    client = _get_client(ctx)
    try:
        data = columns_mod.update_column(client, column_id, name=name)
        click.echo(json.dumps(data, indent=2) if ctx.obj.get("as_json") else f"Column updated.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@columns.command("delete")
@click.argument("column_id")
@click.confirmation_option(prompt="Are you sure you want to delete this column?")
@click.pass_context
def columns_delete(ctx, column_id):
    """Delete a column."""
    client = _get_client(ctx)
    try:
        columns_mod.delete_column(client, column_id)
        click.echo("Column deleted.")
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── Comment commands ──────────────────────────────────────────────────


@cli.group()
def comments():
    """Comment management commands."""
    pass


@comments.command("list")
@click.argument("card_number")
@click.pass_context
def comments_list(ctx, card_number):
    """List comments on a card."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = comments_mod.list_comments(client, card_number)
        output(data, format_comments, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@comments.command("add")
@click.argument("card_number")
@click.argument("body")
@click.pass_context
def comments_add(ctx, card_number, body):
    """Add a comment to a card."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = comments_mod.create_comment(client, card_number, body)
        if as_json:
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            click.echo("Comment added.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@comments.command("update")
@click.argument("card_number")
@click.argument("comment_id")
@click.argument("body")
@click.pass_context
def comments_update(ctx, card_number, comment_id, body):
    """Update a comment."""
    client = _get_client(ctx)
    try:
        comments_mod.update_comment(client, card_number, comment_id, body)
        click.echo("Comment updated.")
    except FizzyAPIError as e:
        _handle_api_error(e)


@comments.command("delete")
@click.argument("card_number")
@click.argument("comment_id")
@click.confirmation_option(prompt="Delete this comment?")
@click.pass_context
def comments_delete(ctx, card_number, comment_id):
    """Delete a comment."""
    client = _get_client(ctx)
    try:
        comments_mod.delete_comment(client, card_number, comment_id)
        click.echo("Comment deleted.")
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── Tag commands ──────────────────────────────────────────────────────


@cli.group()
def tags():
    """Tag management commands."""
    pass


@tags.command("list")
@click.pass_context
def tags_list(ctx):
    """List all tags."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = tags_mod.list_tags(client)
        output(data, format_tags, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


# ── User commands ─────────────────────────────────────────────────────


@cli.group()
def users():
    """User management commands."""
    pass


@users.command("list")
@click.pass_context
def users_list(ctx):
    """List all users."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = users_mod.list_users(client)
        output(data, format_users, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)


@users.command("show")
@click.argument("user_id")
@click.pass_context
def users_show(ctx, user_id):
    """Show a user's details."""
    client = _get_client(ctx)
    as_json = ctx.obj.get("as_json", False)
    try:
        data = users_mod.get_user(client, user_id)
        output(data, format_user, as_json)
    except FizzyAPIError as e:
        _handle_api_error(e)
