"""Column operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_columns(client: FizzyClient, board_id: str) -> list:
    """List all columns for a board."""
    return client.get(f"/boards/{board_id}/columns")


def create_column(client: FizzyClient, board_id: str, name: str) -> dict:
    """Create a new column on a board."""
    return client.post(f"/boards/{board_id}/columns", {"column": {"name": name}})


def update_column(client: FizzyClient, column_id: str, **kwargs) -> dict:
    """Update a column. Pass keyword args for fields to update."""
    return client.patch(f"/columns/{column_id}", {"column": kwargs})


def delete_column(client: FizzyClient, column_id: str):
    """Delete a column."""
    return client.delete(f"/columns/{column_id}")
