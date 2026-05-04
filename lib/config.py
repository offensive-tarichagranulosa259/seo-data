"""Config storage for seo-data skill.

Stores all tokens, API keys, and selected properties under ~/.seo-data/.
Uses a single config.json file with a stable schema so it can be reasoned
about by `status.py` without provider-specific code paths.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".seo-data"
CONFIG_FILE = CONFIG_DIR / "config.json"
GOOGLE_CLIENT_FILE = CONFIG_DIR / "google_client.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "google": {
        "tokens": None,
        "gsc_site": None,
        "ga4_property": None,
    },
    "bing": {
        "api_key": None,
        "site": None,
    },
}


def ensure_config_dir() -> Path:
    """Create the config dir if missing. On POSIX, set 0o700 perms."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        try:
            os.chmod(CONFIG_DIR, stat.S_IRWXU)
        except OSError:
            pass
    return CONFIG_DIR


def load_config() -> dict[str, Any]:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        return _deep_copy(DEFAULT_CONFIG)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _deep_copy(DEFAULT_CONFIG)
    return _merge_defaults(data, DEFAULT_CONFIG)


def save_config(config: dict[str, Any]) -> None:
    ensure_config_dir()
    fd, tmp_path = tempfile.mkstemp(dir=str(CONFIG_DIR), prefix=".config.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        os.replace(tmp_path, CONFIG_FILE)
        if os.name == "posix":
            try:
                os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def update(section: str, **fields: Any) -> dict[str, Any]:
    """Update one section atomically. Returns the new full config."""
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section].update(fields)
    save_config(config)
    return config


def clear_section(section: str) -> None:
    """Reset a section back to defaults (used by disconnect)."""
    config = load_config()
    config[section] = _deep_copy(DEFAULT_CONFIG.get(section, {}))
    save_config(config)


def _deep_copy(obj: Any) -> Any:
    return json.loads(json.dumps(obj))


def _merge_defaults(data: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    """Merge loaded data over defaults so missing keys get filled in."""
    merged = _deep_copy(defaults)
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _merge_defaults(v, merged[k])
        else:
            merged[k] = v
    return merged
