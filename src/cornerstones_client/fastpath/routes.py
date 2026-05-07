from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class RouteSpec:
    method: str
    path: str
    params: dict[str, Any]
    auth_required: bool = True
    timeout: float = 15.0


_INT_FIELDS = {"count", "bars", "bars_count"}


def _parse_flags(
    tokens: Sequence[str],
    *,
    defaults: dict[str, Any],
    allowed: set[str],
) -> dict[str, Any] | None:
    params = dict(defaults)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"-h", "--help"}:
            return None
        if not token.startswith("--"):
            return None
        name = token[2:].replace("-", "_")
        if name not in allowed:
            return None
        if index + 1 >= len(tokens):
            return None
        value: Any = tokens[index + 1]
        if str(value).startswith("--"):
            return None
        if name in _INT_FIELDS:
            try:
                value = int(value)
            except ValueError:
                return None
        params[name] = value
        index += 2
    return params


def _no_flags(tokens: Sequence[str]) -> bool:
    return not tokens or tokens == ["--"]


def _spec(path: str, params: dict[str, Any] | None = None, *, auth_required: bool = True, timeout: float = 15.0) -> RouteSpec:
    return RouteSpec("GET", path, params or {}, auth_required=auth_required, timeout=timeout)


def match_route(argv: Sequence[str]) -> RouteSpec | None:
    """Return a fast-path request spec for Phase-1 read-only CLI argv.

    ``None`` means unsupported: caller must fall back to the legacy core CLI.
    """
    tokens = list(argv)
    if not tokens or tokens[0] in {"-h", "--help"}:
        return None

    if tokens[:2] == ["health", "status"] and _no_flags(tokens[2:]):
        return _spec("/health", auth_required=False, timeout=5.0)

    if tokens[:2] == ["context", "fx"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "EURUSD", "timeframe": "1h", "count": 3},
            allowed={"symbol", "timeframe", "count"},
        )
        return None if params is None else _spec("/v1/context/fx", params)

    if tokens[:2] == ["context", "gold"]:
        return _spec("/v1/context/gold") if _no_flags(tokens[2:]) else None

    if tokens[:2] == ["gold", "context"]:
        return _spec("/v1/gold/context") if _no_flags(tokens[2:]) else None

    if tokens[:2] == ["cross-asset", "context"]:
        return _spec("/v1/cross-asset/context") if _no_flags(tokens[2:]) else None

    if tokens[:2] == ["fx", "quote"]:
        params = _parse_flags(tokens[2:], defaults={"symbol": "EURUSD"}, allowed={"symbol"})
        return None if params is None else _spec("/v1/fx/quote", params)

    if tokens[:2] == ["fx", "bars"]:
        params = _parse_flags(tokens[2:], defaults={"symbol": "EURUSD", "timeframe": "H1"}, allowed={"symbol", "timeframe"})
        return None if params is None else _spec("/v1/fx/bars", params)

    if tokens[:2] == ["fx", "indicators"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "EURUSD", "timeframe": "H1", "bars": 200},
            allowed={"symbol", "timeframe", "bars"},
        )
        return None if params is None else _spec("/v1/fx/indicators", params)

    if tokens[:2] == ["fx", "session"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "EURUSD", "timeframe": "H1", "bars": 200},
            allowed={"symbol", "timeframe", "bars"},
        )
        return None if params is None else _spec("/v1/fx/session", params)

    if tokens[:2] == ["stocks", "quote"]:
        params = _parse_flags(tokens[2:], defaults={"symbol": "AAPL"}, allowed={"symbol"})
        return None if params is None else _spec("/v1/stocks/quote", params)

    if tokens[:2] == ["stocks", "context"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "AAPL", "bars_count": 5},
            allowed={"symbol", "bars_count"},
        )
        return None if params is None else _spec("/v1/stocks/context", params)

    return None
