"""Card operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def create_card(
    client: FizzyClient,
    board_id: str,
    title: str,
    column_id: str | None = None,
) -> dict:
    """Create a new card on a board."""
    data = {"card": {"title": title}}
    if column_id:
        data["card"]["column_id"] = column_id
    return client.post(f"/boards/{board_id}/cards", data)


def get_card(client: FizzyClient, card_number: int | str) -> dict:
    """Get a card by its number."""
    return client.get(f"/cards/{card_number}")


def update_card(client: FizzyClient, card_number: int | str, **kwargs) -> dict:
    """Update a card. Pass keyword args for fields to update."""
    return client.patch(f"/cards/{card_number}", {"card": kwargs})


def delete_card(client: FizzyClient, card_number: int | str):
    """Delete a card."""
    return client.delete(f"/cards/{card_number}")


def close_card(client: FizzyClient, card_number: int | str):
    """Close a card."""
    return client.post(f"/cards/{card_number}/closure")


def reopen_card(client: FizzyClient, card_number: int | str):
    """Reopen a closed card."""
    return client.delete(f"/cards/{card_number}/closure")


def move_card(client: FizzyClient, card_number: int | str, column_id: str):
    """Move a card to a different column."""
    return client.patch(f"/cards/{card_number}/column", {"column_id": column_id})


def assign_user(client: FizzyClient, card_number: int | str, user_id: str):
    """Assign a user to a card."""
    return client.post(
        f"/cards/{card_number}/assignments",
        {"assignment": {"user_id": user_id}},
    )


def unassign_user(
    client: FizzyClient, card_number: int | str, assignment_id: str
):
    """Remove a user assignment from a card."""
    return client.delete(f"/cards/{card_number}/assignments/{assignment_id}")
