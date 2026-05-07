from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:8100"
DEFAULT_CLIENT_API_BASE_URL = "https://api.usecornerstones.com"


@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str | None
    source: str = "core_default"


def _xdg_config_home() -> Path:
    xdg = os.getenv("XDG_CONFIG_HOME")
    return Path(xdg).expanduser() if xdg else Path.home() / ".config"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                return data
    except Exception:
        return {}
    return {}


def _has_payload(payload: dict[str, Any]) -> bool:
    return any(value not in (None, "", [], {}) for value in payload.values())


def load_runtime_config() -> RuntimeConfig:
    """Load core-compatible base URL and bearer without importing core CLI.

    Source pairing is intentional:
    - explicit env base URL uses only an explicit env bearer;
    - core config/credentials stay paired together;
    - client config is used only when no core state exists.
    This avoids sending a stored bearer to a different env/client host.
    """
    home = _xdg_config_home()
    core_config = _load_json(home / "cornerstones" / "config.json")
    core_credentials = _load_json(home / "cornerstones" / "credentials.json")
    client_config = _load_json(home / "cornerstones-client" / "config.json")

    env_base_url = os.getenv("CORNERSTONES_BASE_URL") or os.getenv("CORNERSTONES_API_BASE_URL")
    env_api_key = os.getenv("CORNERSTONES_API_KEY")

    fastpath_default_url = os.getenv("CORNERSTONES_FASTPATH_DEFAULT_BASE_URL") or DEFAULT_LOCAL_BASE_URL

    if env_base_url:
        return RuntimeConfig(
            str(env_base_url).rstrip("/"),
            str(env_api_key) if env_api_key else None,
            source="env",
        )

    if _has_payload(core_config) or _has_payload(core_credentials):
        api_key = core_credentials.get("api_key") or env_api_key
        return RuntimeConfig(
            str(core_config.get("base_url") or fastpath_default_url).rstrip("/"),
            str(api_key) if api_key else None,
            source="core",
        )

    if _has_payload(client_config):
        api_key = client_config.get("api_key") or env_api_key
        return RuntimeConfig(
            str(client_config.get("api_base_url") or DEFAULT_CLIENT_API_BASE_URL).rstrip("/"),
            str(api_key) if api_key else None,
            source="client",
        )

    return RuntimeConfig(str(fastpath_default_url).rstrip("/"), str(env_api_key) if env_api_key else None, source="core_default")
