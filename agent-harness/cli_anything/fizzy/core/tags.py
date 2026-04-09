"""Tag operations for Fizzy."""

from cli_anything.fizzy.core.client import FizzyClient


def list_tags(client: FizzyClient) -> list:
    """List all tags."""
    return client.get("/tags")
