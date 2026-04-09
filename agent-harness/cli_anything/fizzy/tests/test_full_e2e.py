"""End-to-end tests for cli-anything-fizzy against a live Fizzy instance.

Requires environment variables:
  FIZZY_ACCESS_TOKEN  — Bearer token with write permissions
  FIZZY_BASE_URL      — Base URL (default: https://tasks.baum.to)

Skip all tests if FIZZY_ACCESS_TOKEN is not set.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

SKIP_REASON = "FIZZY_ACCESS_TOKEN not set — skipping E2E tests"
pytestmark = pytest.mark.skipif(
    not os.environ.get("FIZZY_ACCESS_TOKEN"),
    reason=SKIP_REASON,
)


class TestCLISubprocess:
    """Run the CLI as a subprocess, like a real user would."""

    @staticmethod
    def _resolve_cli(name: str) -> str:
        """Find the CLI executable."""
        path = shutil.which(name)
        if path:
            return path
        # Fallback: run as python module
        return None

    @classmethod
    def _run(cls, *args, expect_success=True) -> subprocess.CompletedProcess:
        """Run the CLI with given arguments."""
        cli_path = cls._resolve_cli("cli-anything-fizzy")
        if cli_path:
            cmd = [cli_path] + list(args)
        else:
            cmd = [sys.executable, "-m", "cli_anything.fizzy"] + list(args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ},
        )
        if expect_success:
            assert result.returncode == 0, (
                f"CLI failed with rc={result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        return result

    # ── Basic tests ───────────────────────────────────────────────────

    def test_help(self):
        result = self._run("--help")
        assert "Fizzy" in result.stdout or "fizzy" in result.stdout
        assert "boards" in result.stdout

    def test_version(self):
        result = self._run("--version")
        assert "1.0.0" in result.stdout

    # ── Auth tests ────────────────────────────────────────────────────

    def test_auth_whoami(self):
        result = self._run("auth", "whoami")
        assert "User:" in result.stdout or "id" in result.stdout.lower()

    def test_auth_whoami_json(self):
        result = self._run("--json", "auth", "whoami")
        data = json.loads(result.stdout)
        assert "id" in data or "name" in data

    # ── Board tests ───────────────────────────────────────────────────

    def test_boards_list(self):
        result = self._run("boards", "list")
        # Should at least have the header row
        assert "ID" in result.stdout or "No boards" in result.stdout

    def test_boards_list_json(self):
        result = self._run("--json", "boards", "list")
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    # ── Tag tests ─────────────────────────────────────────────────────

    def test_tags_list(self):
        result = self._run("tags", "list")
        assert result.returncode == 0

    # ── User tests ────────────────────────────────────────────────────

    def test_users_list(self):
        result = self._run("users", "list")
        assert result.returncode == 0

    # ── Card lifecycle test ───────────────────────────────────────────

    def test_card_lifecycle(self):
        """Create a card, show it, close it, reopen it, then delete it."""
        # First, get a board to create the card on
        result = self._run("--json", "boards", "list")
        boards = json.loads(result.stdout)
        if not boards:
            pytest.skip("No boards available for card lifecycle test")

        board_id = boards[0]["id"]

        # Create card
        result = self._run("--json", "cards", "create", board_id, "E2E Test Card")
        card = json.loads(result.stdout)
        card_number = str(card["number"])

        try:
            # Show card
            result = self._run("--json", "cards", "show", card_number)
            shown = json.loads(result.stdout)
            assert shown["title"] == "E2E Test Card"

            # Close card
            result = self._run("cards", "close", card_number)
            assert "closed" in result.stdout.lower()

            # Reopen card
            result = self._run("cards", "reopen", card_number)
            assert "reopened" in result.stdout.lower()

        finally:
            # Clean up — delete the card (need --yes to bypass confirmation)
            self._run("cards", "delete", card_number, "--yes", expect_success=False)

    # ── Columns test ──────────────────────────────────────────────────

    def test_columns_list(self):
        """List columns for the first available board."""
        result = self._run("--json", "boards", "list")
        boards = json.loads(result.stdout)
        if not boards:
            pytest.skip("No boards available")

        board_id = boards[0]["id"]
        result = self._run("columns", "list", board_id)
        assert result.returncode == 0
