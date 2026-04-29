"""Card operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_cards(
    client: FizzyClient,
    board_ids: list[str] | None = None,
    assignee_ids: list[str] | None = None,
    tag_ids: list[str] | None = None,
    indexed_by: str | None = None,
    sorted_by: str | None = None,
) -> list:
    """List cards with optional filters."""
    params = {}
    if board_ids:
        params["board_ids[]"] = board_ids
    if assignee_ids:
        params["assignee_ids[]"] = assignee_ids
    if tag_ids:
        params["tag_ids[]"] = tag_ids
    if indexed_by:
        params["indexed_by"] = indexed_by
    if sorted_by:
        params["sorted_by"] = sorted_by
    return client.get("/cards", params=params)


def create_card(
    client: FizzyClient,
    board_id: str,
    title: str,
    description: str | None = None,
    tag_ids: list[str] | None = None,
) -> dict:
    """Create a new card on a board."""
    data = {"card": {"title": title}}
    if description:
        data["card"]["description"] = description
    if tag_ids:
        data["card"]["tag_ids"] = tag_ids
    return client.post(f"/boards/{board_id}/cards", data)


def get_card(client: FizzyClient, card_number: int | str) -> dict:
    """Get a card by its number."""
    return client.get(f"/cards/{card_number}")


def update_card(client: FizzyClient, card_number: int | str, **kwargs) -> dict:
    """Update a card. Pass keyword args for fields to update."""
    return client.put(f"/cards/{card_number}", {"card": kwargs})


def delete_card(client: FizzyClient, card_number: int | str):
    """Delete a card."""
    return client.delete(f"/cards/{card_number}")


def close_card(client: FizzyClient, card_number: int | str):
    """Close a card (move to Done)."""
    return client.post(f"/cards/{card_number}/closure")


def reopen_card(client: FizzyClient, card_number: int | str):
    """Reopen a closed card."""
    return client.delete(f"/cards/{card_number}/closure")


def triage_card(client: FizzyClient, card_number: int | str, column_id: str):
    """Move a card into a column."""
    return client.post(f"/cards/{card_number}/triage", {"column_id": column_id})


def untriage_card(client: FizzyClient, card_number: int | str):
    """Send a card back to triage (Maybe?)."""
    return client.delete(f"/cards/{card_number}/triage")


def not_now_card(client: FizzyClient, card_number: int | str):
    """Move a card to Not Now."""
    return client.post(f"/cards/{card_number}/not_now")


def move_card(client: FizzyClient, card_number: int | str, column_id: str):
    """Move a card to a different column (alias for triage_card)."""
    return triage_card(client, card_number, column_id)


def assign_user(client: FizzyClient, card_number: int | str, user_id: str):
    """Toggle assignment of a user to/from a card."""
    return client.post(
        f"/cards/{card_number}/assignments",
        {"assignee_id": user_id},
    )


def unassign_user(
    client: FizzyClient, card_number: int | str, user_id: str
):
    """Remove a user assignment from a card (toggles off)."""
    return assign_user(client, card_number, user_id)


def toggle_tag(client: FizzyClient, card_number: int | str, tag_title: str):
    """Toggle a tag on/off for a card."""
    return client.post(
        f"/cards/{card_number}/taggings",
        {"tag_title": tag_title},
    )


def watch_card(client: FizzyClient, card_number: int | str):
    """Subscribe to notifications for a card."""
    return client.post(f"/cards/{card_number}/watch")


def unwatch_card(client: FizzyClient, card_number: int | str):
    """Unsubscribe from notifications for a card."""
    return client.delete(f"/cards/{card_number}/watch")
