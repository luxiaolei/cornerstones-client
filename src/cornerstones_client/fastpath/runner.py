from __future__ import annotations

import json
import sys
from typing import Any, Sequence

from .config import load_runtime_config
from .http import FastPathFallback, FastPathHTTPError, FastPathRequestFailed, MissingAuth, request_json
from ..public_safety import sanitize_public_payload
from .routes import match_route


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(sanitize_public_payload(payload), indent=2, ensure_ascii=False))


def run(argv: Sequence[str] | None = None) -> int | None:
    """Run Phase-1 fast path.

    Returns:
        ``0``/``1`` when argv was handled; ``None`` when legacy CLI must run.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    spec = match_route(args)
    if spec is None:
        return None

    try:
        config = load_runtime_config()
        payload = request_json(spec, config)
    except MissingAuth:
        _print({"error": "not_logged_in", "message": "run `cornerstones auth login --api-key ...` first"})
        return 1
    except FastPathFallback:
        if "config" in locals() and config.source == "env" and (spec.auth_required or spec.path.startswith("/v1/")):
            _print(
                {
                    "error": "fastpath_unavailable",
                    "message": "env-configured API route unavailable; refusing legacy fallback to preserve credential source pairing",
                }
            )
            return 1
        return None
    except FastPathHTTPError as exc:
        _print(exc.payload())
        return 1
    except FastPathRequestFailed as exc:
        _print(exc.payload())
        return 1
    except Exception:
        if "config" in locals() and config.source == "env" and (spec.auth_required or spec.path.startswith("/v1/")):
            _print(
                {
                    "error": "fastpath_unavailable",
                    "message": "env-configured API route failed; refusing legacy fallback to preserve credential source pairing",
                }
            )
            return 1
        raise

    _print(payload)
    return 0
