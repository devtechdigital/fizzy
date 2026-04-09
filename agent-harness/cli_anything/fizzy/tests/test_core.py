"""Unit tests for cli-anything-fizzy core modules.

All HTTP calls are mocked — no network required.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from cli_anything.fizzy.core.config import (
    DEFAULT_CONFIG,
    load_config,
    save_config,
    get_config,
    get_config_with_env,
)
from cli_anything.fizzy.core.client import FizzyClient, FizzyAPIError
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


# ── Helpers ───────────────────────────────────────────────────────────


def _mock_response(status_code=200, json_data=None, text=""):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = json.dumps(json_data).encode() if json_data is not None else b""
    resp.json.return_value = json_data
    resp.text = text
    return resp


def _make_client():
    """Create a FizzyClient with a mocked session."""
    client = FizzyClient("https://example.com", "test-token")
    client.session = MagicMock()
    return client


# ── Config Tests ──────────────────────────────────────────────────────


class TestConfig:
    def test_default_config(self):
        assert DEFAULT_CONFIG["base_url"] == "https://tasks.baum.to"
        assert DEFAULT_CONFIG["access_token"] == ""

    def test_load_config_missing_file(self, tmp_path):
        with patch("cli_anything.fizzy.core.config.CONFIG_FILE", tmp_path / "nope.json"):
            config = load_config()
        assert config["base_url"] == "https://tasks.baum.to"
        assert config["access_token"] == ""

    def test_save_and_load_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_dir = tmp_path

        with patch("cli_anything.fizzy.core.config.CONFIG_FILE", config_file), \
             patch("cli_anything.fizzy.core.config.CONFIG_DIR", config_dir):
            save_config({"base_url": "https://test.local", "access_token": "abc123"})
            loaded = load_config()

        assert loaded["base_url"] == "https://test.local"
        assert loaded["access_token"] == "abc123"

    def test_get_config_no_token(self, tmp_path):
        with patch("cli_anything.fizzy.core.config.CONFIG_FILE", tmp_path / "nope.json"):
            with pytest.raises(RuntimeError, match="not configured"):
                get_config()

    def test_get_config_with_env(self, tmp_path):
        with patch("cli_anything.fizzy.core.config.CONFIG_FILE", tmp_path / "nope.json"), \
             patch.dict(os.environ, {"FIZZY_ACCESS_TOKEN": "env-token", "FIZZY_BASE_URL": "https://env.local"}):
            config = get_config_with_env()
        assert config["access_token"] == "env-token"
        assert config["base_url"] == "https://env.local"


# ── Client Tests ──────────────────────────────────────────────────────


class TestClient:
    def test_client_headers(self):
        client = FizzyClient("https://example.com", "my-token")
        headers = client.session.headers
        assert headers["Authorization"] == "Bearer my-token"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_client_get(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, {"ok": True})
        result = client.get("/test")
        assert result == {"ok": True}
        client.session.get.assert_called_once_with("https://example.com/test", params=None)

    def test_client_post(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"id": "123"})
        result = client.post("/test", {"name": "foo"})
        assert result == {"id": "123"}
        client.session.post.assert_called_once_with(
            "https://example.com/test", json={"name": "foo"}
        )

    def test_client_patch(self):
        client = _make_client()
        client.session.patch.return_value = _mock_response(200, {"updated": True})
        result = client.patch("/test/1", {"name": "bar"})
        assert result == {"updated": True}

    def test_client_delete(self):
        client = _make_client()
        client.session.delete.return_value = _mock_response(204)
        result = client.delete("/test/1")
        assert result is None

    def test_client_401(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(401, {"error": "unauthorized"})
        with pytest.raises(FizzyAPIError) as exc_info:
            client.get("/test")
        assert exc_info.value.status_code == 401
        assert "Authentication" in str(exc_info.value)

    def test_client_403(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(403, {"error": "forbidden"})
        with pytest.raises(FizzyAPIError) as exc_info:
            client.get("/test")
        assert exc_info.value.status_code == 403
        assert "Permission" in str(exc_info.value)

    def test_client_404(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(404, {"error": "not found"})
        with pytest.raises(FizzyAPIError) as exc_info:
            client.get("/test")
        assert exc_info.value.status_code == 404

    def test_client_422(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(422, {"errors": ["title is blank"]})
        with pytest.raises(FizzyAPIError) as exc_info:
            client.post("/test", {})
        assert exc_info.value.status_code == 422
        assert "Validation" in str(exc_info.value)

    def test_client_500(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(500, {"error": "internal"})
        with pytest.raises(FizzyAPIError) as exc_info:
            client.get("/test")
        assert exc_info.value.status_code == 500


# ── Board Module Tests ────────────────────────────────────────────────


class TestBoards:
    def test_list_boards(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, [{"id": "b1", "name": "Board 1"}])
        result = boards_mod.list_boards(client)
        assert len(result) == 1
        assert result[0]["name"] == "Board 1"

    def test_get_board(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, {"id": "b1", "name": "Board 1"})
        result = boards_mod.get_board(client, "b1")
        assert result["id"] == "b1"

    def test_create_board(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"id": "b2", "name": "New"})
        result = boards_mod.create_board(client, "New")
        assert result["name"] == "New"
        call_args = client.session.post.call_args
        assert call_args[1]["json"] == {"board": {"name": "New"}}

    def test_delete_board(self):
        client = _make_client()
        client.session.delete.return_value = _mock_response(204)
        result = boards_mod.delete_board(client, "b1")
        assert result is None


# ── Card Module Tests ─────────────────────────────────────────────────


class TestCards:
    def test_create_card(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"number": 1, "title": "Test"})
        result = cards_mod.create_card(client, "b1", "Test")
        assert result["title"] == "Test"
        call_args = client.session.post.call_args
        assert "/boards/b1/cards" in call_args[0][0]

    def test_get_card(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, {"number": 42, "title": "My Card"})
        result = cards_mod.get_card(client, 42)
        assert result["number"] == 42

    def test_close_card(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(200, {"status": "closed"})
        result = cards_mod.close_card(client, 42)
        assert result["status"] == "closed"
        call_args = client.session.post.call_args
        assert "/cards/42/closure" in call_args[0][0]

    def test_reopen_card(self):
        client = _make_client()
        client.session.delete.return_value = _mock_response(204)
        result = cards_mod.reopen_card(client, 42)
        assert result is None
        call_args = client.session.delete.call_args
        assert "/cards/42/closure" in call_args[0][0]

    def test_move_card(self):
        client = _make_client()
        client.session.patch.return_value = _mock_response(200, {"column_id": "col2"})
        result = cards_mod.move_card(client, 42, "col2")
        call_args = client.session.patch.call_args
        assert "/cards/42/column" in call_args[0][0]
        assert call_args[1]["json"] == {"column_id": "col2"}

    def test_assign_user(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"id": "a1"})
        result = cards_mod.assign_user(client, 42, "user1")
        call_args = client.session.post.call_args
        assert "/cards/42/assignments" in call_args[0][0]


# ── Column Module Tests ───────────────────────────────────────────────


class TestColumns:
    def test_list_columns(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, [{"id": "c1", "name": "Todo"}])
        result = columns_mod.list_columns(client, "b1")
        assert len(result) == 1
        call_args = client.session.get.call_args
        assert "/boards/b1/columns" in call_args[0][0]

    def test_create_column(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"id": "c2", "name": "Done"})
        result = columns_mod.create_column(client, "b1", "Done")
        assert result["name"] == "Done"


# ── Comment Module Tests ──────────────────────────────────────────────


class TestComments:
    def test_list_comments(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, [{"id": "cm1", "body": "Hello"}])
        result = comments_mod.list_comments(client, 42)
        assert len(result) == 1

    def test_create_comment(self):
        client = _make_client()
        client.session.post.return_value = _mock_response(201, {"id": "cm2", "body": "Test"})
        result = comments_mod.create_comment(client, 42, "Test")
        assert result["body"] == "Test"
        call_args = client.session.post.call_args
        assert call_args[1]["json"] == {"comment": {"body": "Test"}}


# ── Tag Module Tests ──────────────────────────────────────────────────


class TestTags:
    def test_list_tags(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, [{"id": "t1", "name": "bug"}])
        result = tags_mod.list_tags(client)
        assert len(result) == 1
        assert result[0]["name"] == "bug"


# ── User Module Tests ─────────────────────────────────────────────────


class TestUsers:
    def test_list_users(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, [{"id": "u1", "name": "Alice"}])
        result = users_mod.list_users(client)
        assert len(result) == 1

    def test_get_user(self):
        client = _make_client()
        client.session.get.return_value = _mock_response(200, {"id": "u1", "name": "Alice"})
        result = users_mod.get_user(client, "u1")
        assert result["name"] == "Alice"


# ── Formatter Tests ───────────────────────────────────────────────────


class TestFormatters:
    def test_format_boards(self):
        boards = [{"id": "b1", "name": "Board 1"}, {"id": "b2", "name": "Board 2"}]
        result = format_boards(boards)
        assert "Board 1" in result
        assert "Board 2" in result

    def test_format_boards_empty(self):
        assert "No boards" in format_boards([])

    def test_format_board(self):
        board = {"id": "b1", "name": "My Board", "columns": [{"id": "c1", "name": "Todo"}]}
        result = format_board(board)
        assert "My Board" in result
        assert "Todo" in result

    def test_format_card(self):
        card = {
            "number": 42,
            "title": "Fix Bug",
            "status": "started",
            "id": "card-uuid",
            "board": {"name": "Dev"},
            "column": {"name": "In Progress"},
            "creator": {"name": "Alice"},
            "assignees": [{"name": "Bob"}],
            "tags": [{"name": "bug"}],
        }
        result = format_card(card)
        assert "#42" in result
        assert "Fix Bug" in result
        assert "started" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "bug" in result

    def test_format_cards_empty(self):
        assert "No cards" in format_cards([])

    def test_format_cards(self):
        cards = [{"number": 1, "title": "Card 1", "status": "drafted"}]
        result = format_cards(cards)
        assert "Card 1" in result
        assert "drafted" in result

    def test_format_columns(self):
        cols = [{"id": "c1", "name": "Todo", "position": 0}]
        result = format_columns(cols)
        assert "Todo" in result

    def test_format_columns_empty(self):
        assert "No columns" in format_columns([])

    def test_format_comments(self):
        comments = [{"id": "cm1", "body": "Great work!", "creator": {"name": "Alice"}, "created_at": "2024-01-01"}]
        result = format_comments(comments)
        assert "Great work!" in result
        assert "Alice" in result

    def test_format_comments_empty(self):
        assert "No comments" in format_comments([])

    def test_format_tags(self):
        tags = [{"id": "t1", "name": "bug"}]
        result = format_tags(tags)
        assert "bug" in result

    def test_format_users(self):
        users = [{"id": "u1", "name": "Alice"}]
        result = format_users(users)
        assert "Alice" in result

    def test_format_user(self):
        user = {"id": "u1", "name": "Alice", "email": "alice@example.com"}
        result = format_user(user)
        assert "Alice" in result
        assert "alice@example.com" in result

    def test_output_json(self, capsys):
        data = [{"id": "b1", "name": "Board"}]
        output(data, format_boards, as_json=True)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed[0]["name"] == "Board"

    def test_output_human(self, capsys):
        data = [{"id": "b1", "name": "Board"}]
        output(data, format_boards, as_json=False)
        captured = capsys.readouterr()
        assert "Board" in captured.out
