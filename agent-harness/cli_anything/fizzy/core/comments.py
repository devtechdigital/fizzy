"""Comment operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_comments(client: FizzyClient, card_number: int | str) -> list:
    """List comments on a card."""
    return client.get(f"/cards/{card_number}/comments")


def create_comment(
    client: FizzyClient, card_number: int | str, body: str
) -> dict:
    """Create a comment on a card."""
    return client.post(
        f"/cards/{card_number}/comments",
        {"comment": {"body": body}},
    )


def update_comment(
    client: FizzyClient, card_number: int | str, comment_id: str, body: str
) -> dict:
    """Update a comment."""
    return client.patch(
        f"/cards/{card_number}/comments/{comment_id}",
        {"comment": {"body": body}},
    )


def delete_comment(
    client: FizzyClient, card_number: int | str, comment_id: str
):
    """Delete a comment."""
    return client.delete(f"/cards/{card_number}/comments/{comment_id}")
