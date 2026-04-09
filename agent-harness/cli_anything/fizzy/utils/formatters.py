"""Human-readable output formatters for Fizzy CLI."""

import json
import click


def _truncate(text: str, length: int = 50) -> str:
    """Truncate text to a maximum length."""
    if not text:
        return ""
    text = str(text).replace("\n", " ")
    if len(text) > length:
        return text[: length - 3] + "..."
    return text


def format_boards(boards: list) -> str:
    """Format a list of boards as a table."""
    if not boards:
        return "No boards found."
    lines = []
    lines.append(f"{'ID':<38} {'Name':<30} {'Cards':<8}")
    lines.append("-" * 78)
    for b in boards:
        bid = str(b.get("id", ""))[:36]
        name = _truncate(b.get("name", ""), 28)
        cards = str(b.get("cards_count", b.get("cards", {}).get("count", "")))
        lines.append(f"{bid:<38} {name:<30} {cards:<8}")
    return "\n".join(lines)


def format_board(board: dict) -> str:
    """Format a single board detail view."""
    lines = []
    lines.append(f"Board: {board.get('name', 'Unknown')}")
    lines.append(f"  ID:   {board.get('id', '')}")
    if "columns" in board:
        cols = board["columns"]
        if isinstance(cols, list):
            lines.append(f"  Columns: {len(cols)}")
            for col in cols:
                cname = col.get("name", "")
                lines.append(f"    - {cname} ({col.get('id', '')})")
    return "\n".join(lines)


def format_card(card: dict) -> str:
    """Format a detailed card view."""
    lines = []
    number = card.get("number", "?")
    title = card.get("title", "Untitled")
    status = card.get("status", "unknown")
    lines.append(f"Card #{number}: {title}")
    lines.append(f"  Status:  {status}")
    lines.append(f"  ID:      {card.get('id', '')}")

    if card.get("board"):
        board = card["board"]
        bname = board.get("name", "") if isinstance(board, dict) else str(board)
        lines.append(f"  Board:   {bname}")

    if card.get("column"):
        col = card["column"]
        cname = col.get("name", "") if isinstance(col, dict) else str(col)
        lines.append(f"  Column:  {cname}")

    if card.get("creator"):
        creator = card["creator"]
        cname = creator.get("name", "") if isinstance(creator, dict) else str(creator)
        lines.append(f"  Creator: {cname}")

    if card.get("assignees"):
        assignees = card["assignees"]
        if isinstance(assignees, list):
            names = [
                a.get("name", a.get("id", "")) if isinstance(a, dict) else str(a)
                for a in assignees
            ]
            lines.append(f"  Assigned: {', '.join(names)}")

    if card.get("tags"):
        tags = card["tags"]
        if isinstance(tags, list):
            tag_names = [
                t.get("name", "") if isinstance(t, dict) else str(t)
                for t in tags
            ]
            lines.append(f"  Tags:    {', '.join(tag_names)}")

    if card.get("body"):
        lines.append(f"  Body:    {_truncate(card['body'], 80)}")

    return "\n".join(lines)


def format_cards(cards: list) -> str:
    """Format a list of cards as a table."""
    if not cards:
        return "No cards found."
    lines = []
    lines.append(f"{'#':<8} {'Title':<40} {'Status':<12}")
    lines.append("-" * 62)
    for c in cards:
        number = str(c.get("number", ""))
        title = _truncate(c.get("title", ""), 38)
        status = c.get("status", "")
        lines.append(f"{number:<8} {title:<40} {status:<12}")
    return "\n".join(lines)


def format_columns(columns: list) -> str:
    """Format a list of columns as a table."""
    if not columns:
        return "No columns found."
    lines = []
    lines.append(f"{'ID':<38} {'Name':<30} {'Position':<10}")
    lines.append("-" * 80)
    for col in columns:
        cid = str(col.get("id", ""))[:36]
        name = _truncate(col.get("name", ""), 28)
        pos = str(col.get("position", ""))
        lines.append(f"{cid:<38} {name:<30} {pos:<10}")
    return "\n".join(lines)


def format_comments(comments: list) -> str:
    """Format a list of comments."""
    if not comments:
        return "No comments found."
    lines = []
    for c in comments:
        author = c.get("creator", c.get("author", {}))
        if isinstance(author, dict):
            author_name = author.get("name", "Unknown")
        else:
            author_name = str(author)
        created = c.get("created_at", "")
        body = c.get("body", "")
        cid = c.get("id", "")
        lines.append(f"[{author_name}] ({created})")
        lines.append(f"  {body}")
        lines.append(f"  id: {cid}")
        lines.append("")
    return "\n".join(lines)


def format_tags(tags: list) -> str:
    """Format a list of tags."""
    if not tags:
        return "No tags found."
    lines = []
    lines.append(f"{'ID':<38} {'Name':<30}")
    lines.append("-" * 70)
    for t in tags:
        tid = str(t.get("id", ""))[:36]
        name = _truncate(t.get("name", ""), 28)
        lines.append(f"{tid:<38} {name:<30}")
    return "\n".join(lines)


def format_users(users: list) -> str:
    """Format a list of users."""
    if not users:
        return "No users found."
    lines = []
    lines.append(f"{'ID':<38} {'Name':<30}")
    lines.append("-" * 70)
    for u in users:
        uid = str(u.get("id", ""))[:36]
        name = _truncate(u.get("name", u.get("email", "")), 28)
        lines.append(f"{uid:<38} {name:<30}")
    return "\n".join(lines)


def format_user(user: dict) -> str:
    """Format a single user detail view."""
    lines = []
    lines.append(f"User: {user.get('name', 'Unknown')}")
    lines.append(f"  ID:    {user.get('id', '')}")
    lines.append(f"  Email: {user.get('email', '')}")
    return "\n".join(lines)


def output(data, formatter_fn, as_json: bool = False):
    """Output data as JSON or human-readable.

    Args:
        data: The data to format.
        formatter_fn: A function that takes data and returns a string.
        as_json: If True, output raw JSON instead.
    """
    if as_json:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(formatter_fn(data))
