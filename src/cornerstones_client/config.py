from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    xdg = os.getenv("XDG_CONFIG_HOME")
    return Path(xdg) / "cornerstones-client" if xdg else Path.home() / ".config" / "cornerstones-client"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


DEFAULT_PORTAL_BASE_URL = "https://www.usecornerstones.com"
DEFAULT_API_BASE_URL = "https://api.usecornerstones.com"


def default_portal_base_url() -> str:
    return os.getenv("CORNERSTONES_PORTAL_BASE_URL") or os.getenv("CORNERSTONES_BASE_URL") or DEFAULT_PORTAL_BASE_URL


def default_api_base_url() -> str:
    return os.getenv("CORNERSTONES_API_BASE_URL") or DEFAULT_API_BASE_URL


def default_config() -> dict[str, Any]:
    return {
        "portal_base_url": default_portal_base_url(),
        "api_base_url": default_api_base_url(),
        "api_key": None,
        "trial_cookie": None,
        "trial_token": None,
    }


def _normalize_config(data: dict[str, Any]) -> dict[str, Any]:
    config = default_config()
    legacy_base_url = data.get("base_url")
    if legacy_base_url and not data.get("portal_base_url"):
        data = dict(data)
        data["portal_base_url"] = legacy_base_url
    config.update(data)
    return config


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return default_config()
    data = json.loads(path.read_text())
    return _normalize_config(data)


def save_config(payload: dict[str, Any]) -> Path:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_config(payload), indent=2))
    return path
