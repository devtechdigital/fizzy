"""Board operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_boards(client: FizzyClient) -> list:
    """List all boards."""
    return client.get("/boards")


def get_board(client: FizzyClient, board_id: str) -> dict:
    """Get a single board by ID."""
    return client.get(f"/boards/{board_id}")


def create_board(client: FizzyClient, name: str) -> dict:
    """Create a new board."""
    return client.post("/boards", {"board": {"name": name}})


def update_board(client: FizzyClient, board_id: str, **kwargs) -> dict:
    """Update a board. Pass keyword args for fields to update."""
    return client.patch(f"/boards/{board_id}", {"board": kwargs})


def delete_board(client: FizzyClient, board_id: str):
    """Delete a board."""
    return client.delete(f"/boards/{board_id}")
