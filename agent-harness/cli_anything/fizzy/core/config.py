"""Configuration management for cli-anything-fizzy."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cli-anything-fizzy"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "base_url": "https://tasks.baum.to",
    "access_token": "",
    "account_prefix": "/1",
}


def _ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from disk, returning defaults if not found."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        config = {**DEFAULT_CONFIG, **stored}
        return config
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    """Save config to disk."""
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_config() -> dict:
    """Return current config or raise if not configured."""
    config = load_config()
    if not config.get("access_token"):
        raise RuntimeError(
            "Fizzy is not configured. Run 'cli-anything-fizzy auth setup' "
            "or set FIZZY_ACCESS_TOKEN environment variable."
        )
    return config


def get_config_with_env() -> dict:
    """Return config, allowing env vars to override file config."""
    config = load_config()
    # Environment variables override file config
    env_token = os.environ.get("FIZZY_ACCESS_TOKEN")
    env_url = os.environ.get("FIZZY_BASE_URL")
    if env_token:
        config["access_token"] = env_token
    if env_url:
        config["base_url"] = env_url
    if not config.get("access_token"):
        raise RuntimeError(
            "Fizzy is not configured. Run 'cli-anything-fizzy auth setup' "
            "or set FIZZY_ACCESS_TOKEN environment variable."
        )
    return config


def setup():
    """Interactive setup — prompts for token and base URL."""
    import click

    config = load_config()

    click.echo("Fizzy CLI Setup")
    click.echo("=" * 40)

    base_url = click.prompt(
        "Base URL",
        default=config.get("base_url", DEFAULT_CONFIG["base_url"]),
    )
    access_token = click.prompt(
        "Access Token (Bearer token)",
        default=config.get("access_token", ""),
        hide_input=True,
    )

    account_prefix = click.prompt(
        "Account prefix (e.g. /1)",
        default=config.get("account_prefix", DEFAULT_CONFIG["account_prefix"]),
    )

    config["base_url"] = base_url.rstrip("/")
    config["access_token"] = access_token
    config["account_prefix"] = account_prefix

    save_config(config)
    click.echo(f"\nConfig saved to {CONFIG_FILE}")
