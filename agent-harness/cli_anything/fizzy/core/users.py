"""User operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_users(client: FizzyClient) -> list:
    """List all users."""
    return client.get("/users")


def get_user(client: FizzyClient, user_id: str) -> dict:
    """Get a single user by ID."""
    return client.get(f"/users/{user_id}")
