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
    json_body: dict[str, Any] | None = None


_INT_FIELDS = {"count", "bars", "bars_count", "limit", "depth", "max_expirations", "num_rows", "since_minutes"}
_FLOAT_FIELDS = {"threshold", "threshold_percentile", "min_confidence"}


def _parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def _flag_name(token: str, aliases: dict[str, str]) -> str | None:
    if token in aliases:
        return aliases[token]
    if token.startswith("--"):
        raw = token[2:]
        if "_" in raw:
            return None
        return raw.replace("-", "_")
    return None


def _parse_flags(
    tokens: Sequence[str],
    *,
    defaults: dict[str, Any],
    allowed: set[str],
    bool_flags: set[str] | None = None,
    name_map: dict[str, str] | None = None,
    choices: dict[str, set[Any]] | None = None,
    aliases: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    params = dict(defaults)
    bool_flags = bool_flags or set()
    name_map = name_map or {}
    choices = choices or {}
    aliases = aliases or {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"-h", "--help"}:
            return None
        name = _flag_name(token, aliases)
        if name is None:
            return None
        api_name = name_map.get(name, name)
        if name not in allowed and api_name not in allowed:
            return None

        if name in bool_flags or api_name in bool_flags:
            params[api_name] = True
            index += 1
            continue

        if index + 1 >= len(tokens):
            return None
        value: Any = tokens[index + 1]
        if str(value).startswith("-"):
            return None
        if _flag_name(str(value), aliases) is not None:
            return None
        if name in _INT_FIELDS or api_name in _INT_FIELDS:
            try:
                value = int(value)
            except ValueError:
                return None
        elif name in _FLOAT_FIELDS or api_name in _FLOAT_FIELDS:
            try:
                value = float(value)
            except ValueError:
                return None
        if api_name in choices and value not in choices[api_name]:
            return None
        params[api_name] = value
        index += 2
    return {key: value for key, value in params.items() if value is not None}


def _no_flags(tokens: Sequence[str]) -> bool:
    return not tokens or tokens == ["--"]


def _spec(
    path: str,
    params: dict[str, Any] | None = None,
    *,
    auth_required: bool = True,
    timeout: float = 15.0,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
) -> RouteSpec:
    return RouteSpec(method, path, params or {}, auth_required=auth_required, timeout=timeout, json_body=json_body)


def _with_required(params: dict[str, Any] | None, *required: str) -> dict[str, Any] | None:
    if params is None:
        return None
    if any(not params.get(name) for name in required):
        return None
    return params


def _string_true_flags(params: dict[str, Any], *names: str) -> dict[str, Any]:
    output = dict(params)
    for name in names:
        if output.get(name) is True:
            output[name] = "true"
    return output


def _bool_value(params: dict[str, Any], name: str) -> dict[str, Any] | None:
    if name not in params:
        return params
    parsed = _parse_bool(str(params[name]))
    if parsed is None:
        return None
    output = dict(params)
    output[name] = parsed
    return output


def _match_macro(tokens: Sequence[str]) -> RouteSpec | None:
    if tokens[:2] == ["macro", "summary"] and _no_flags(tokens[2:]):
        return _spec("/v1/macro/summary")
    if tokens[:2] == ["macro", "yields"] and _no_flags(tokens[2:]):
        return _spec("/v1/macro/yields")
    if tokens[:2] == ["macro", "series"]:
        params = _with_required(
            _parse_flags(
                tokens[2:],
                defaults={},
                allowed={"name"},
                choices={"name": {"us10y_real", "us10y_breakeven"}},
            ),
            "name",
        )
        return None if params is None else _spec("/v1/macro/series", params)
    if tokens[:2] == ["macro", "calendar"]:
        params = _parse_flags(
            tokens[2:],
            defaults={},
            allowed={"from", "from_date", "to", "to_date", "country", "currency", "importance", "category"},
            name_map={"from_date": "from", "to_date": "to"},
            choices={"importance": {"low", "medium", "high"}},
        )
        return None if params is None else _spec("/v1/macro/calendar", params)
    return None


def _match_options(tokens: Sequence[str]) -> RouteSpec | None:
    if tokens[:2] == ["options", "chain"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "AAPL", "option_type": "both", "moneyness": "all", "sort": "moneyness", "preset": "compact"},
            allowed={"symbol", "expiration", "expiration_date", "option_type", "moneyness", "depth", "max_expirations", "include", "sort", "preset"},
            name_map={"expiration": "expiration_date"},
            choices={
                "option_type": {"call", "put", "both"},
                "moneyness": {"all", "itm", "atm", "otm"},
                "sort": {"strike", "oi", "volume", "moneyness"},
                "preset": {"compact", "expanded"},
            },
        )
        return None if params is None else _spec("/v1/options/chain", params, timeout=60.0)
    if tokens[:2] == ["options", "wall"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "AAPL", "threshold_percentile": 90.0},
            allowed={"symbol", "expiration", "expiration_date", "threshold", "threshold_percentile"},
            name_map={"expiration": "expiration_date", "threshold": "threshold_percentile"},
        )
        return None if params is None else _spec("/v1/options/wall", params, timeout=60.0)
    if tokens[:2] == ["options", "analysis"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "AAPL"},
            allowed={"symbol", "expiration", "expiration_date"},
            name_map={"expiration": "expiration_date"},
        )
        return None if params is None else _spec("/v1/options/analysis", params, timeout=60.0)
    return None


def _match_orderflow(tokens: Sequence[str]) -> RouteSpec | None:
    if len(tokens) < 2 or tokens[0] != "orderflow":
        return None
    endpoints = {
        "raw": "/v1/orderflow/raw",
        "summary": "/v1/orderflow/summary",
        "context": "/v1/orderflow/context",
        "historical": "/v1/orderflow/historical",
        "liquidity-metrics": "/v1/orderflow/liquidity-metrics",
    }
    endpoint = endpoints.get(tokens[1])
    if endpoint is None:
        return None
    params = _parse_flags(tokens[2:], defaults={}, allowed={"symbol"}, aliases={"-s": "symbol"})
    return None if params is None else _spec(endpoint, params, timeout=30.0)


def _match_crypto(tokens: Sequence[str]) -> RouteSpec | None:
    if len(tokens) < 2 or tokens[0] != "crypto":
        return None
    surface = tokens[1]
    if surface in {"quote", "ticker"}:
        params = _parse_flags(tokens[2:], defaults={"symbol": "BTCUSDT"}, allowed={"symbol"})
        return None if params is None else _spec(f"/v1/crypto/{surface}", params)
    if surface == "bars":
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "BTCUSDT", "timeframe": "1h", "count": 100},
            allowed={"symbol", "timeframe", "count"},
        )
        return None if params is None else _spec("/v1/crypto/bars", params)
    if surface in {"depth", "trades"}:
        default_limit = 50 if surface == "depth" else 100
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "BTCUSDT", "limit": default_limit},
            allowed={"symbol", "limit"},
        )
        return None if params is None else _spec(f"/v1/crypto/{surface}", params)
    if surface in {"session", "indicators"}:
        params = _parse_flags(
            tokens[2:],
            defaults={"symbol": "BTCUSDT", "timeframe": "1h", "bars": 200},
            allowed={"symbol", "timeframe", "bars"},
        )
        return None if params is None else _spec(f"/v1/crypto/{surface}", params)
    return None


def _match_geopolitics(tokens: Sequence[str]) -> RouteSpec | None:
    if not tokens or tokens[0] != "geopolitics":
        return None
    priority_choices = {"priority": {"low", "medium", "high", "critical"}, "min_priority": {"low", "medium", "high", "critical"}}
    if len(tokens) == 1 or tokens[:2] == ["geopolitics", "status"]:
        return _spec("/v1/geopolitics/status") if _no_flags(tokens[2:]) else None
    if tokens[:2] == ["geopolitics", "osint-feed"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"limit": 20},
            allowed={"limit", "priority", "region"},
            choices=priority_choices,
        )
        return None if params is None else _spec("/v1/geopolitics/osint-feed", params)
    if tokens[:2] == ["geopolitics", "pizza-index"]:
        return _spec("/v1/geopolitics/pizza-index") if _no_flags(tokens[2:]) else None
    if tokens[:2] == ["geopolitics", "polymarket"]:
        params = _parse_flags(tokens[2:], defaults={"limit": 10}, allowed={"limit", "keyword"})
        return None if params is None else _spec("/v1/geopolitics/polymarket", params)
    if tokens[:2] == ["geopolitics", "context"]:
        return _spec("/v1/geopolitics/context") if _no_flags(tokens[2:]) else None
    if tokens[:2] == ["geopolitics", "evidence"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"min_priority": "low"},
            allowed={"min_priority"},
            choices=priority_choices,
        )
        return None if params is None else _spec("/v1/geopolitics/evidence", params)
    return None


def _match_polymarket(tokens: Sequence[str]) -> RouteSpec | None:
    if not tokens or tokens[0] != "polymarket":
        return None
    if len(tokens) == 1 or tokens[:2] == ["polymarket", "overview"]:
        return _spec("/v1/polymarket/overview") if _no_flags(tokens[2:]) else None
    if tokens[:2] == ["polymarket", "context"]:
        return _spec("/v1/polymarket/context") if _no_flags(tokens[2:]) else None
    return None


def _match_alerts(tokens: Sequence[str]) -> RouteSpec | None:
    if len(tokens) < 2 or tokens[0] != "alerts":
        return None
    lane_choices = {"scheduled_macro", "x_pressure", "news_pressure", "cross_source_pressure"}
    priority_choices = {"low", "medium", "high", "critical"}
    lifecycle_choices = {"active", "expired"}
    delivery_choices = {"queued", "delivering", "delivered", "failed", "dead_letter"}
    if tokens[:2] == ["alerts", "recent"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"since_minutes": 60, "limit": 20, "only_active": "false"},
            allowed={"asset", "lane", "kind", "since_minutes", "min_priority", "lifecycle", "delivery_status", "cursor", "only_active", "limit"},
            bool_flags={"only_active"},
            choices={
                "lane": lane_choices,
                "min_priority": priority_choices,
                "lifecycle": lifecycle_choices,
                "delivery_status": delivery_choices,
            },
        )
        if params is None:
            return None
        return _spec("/v1/alerts/recent", _string_true_flags(params, "only_active"))
    if tokens[:2] == ["alerts", "history"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"limit": 50},
            allowed={"asset", "lane", "kind", "min_priority", "lifecycle", "delivery_status", "cursor", "limit"},
            choices={
                "lane": lane_choices,
                "min_priority": priority_choices,
                "lifecycle": lifecycle_choices,
                "delivery_status": delivery_choices,
            },
        )
        return None if params is None else _spec("/v1/alerts/history", params)
    if tokens[:2] == ["alerts", "metrics"]:
        if _no_flags(tokens[2:]):
            return _spec("/v1/alerts/metrics")
        if tokens[2:] == ["--hide-state"]:
            return _spec("/v1/alerts/metrics", {"include_state": "false"})
        return None
    return None


def _match_evidence(tokens: Sequence[str]) -> RouteSpec | None:
    if tokens[:2] != ["evidence", "feed"]:
        return None
    params = _parse_flags(
        tokens[2:],
        defaults={
            "types": ["signal", "alert", "opportunity", "anomaly"],
            "min_priority": "low",
            "limit": 50,
            "raw_evidence_only": "true",
        },
        allowed={"min_priority", "min_confidence", "limit"},
        choices={"min_priority": {"low", "medium", "high", "critical"}},
    )
    return None if params is None else _spec("/v1/evidence/feed", params)


def _match_events(tokens: Sequence[str]) -> RouteSpec | None:
    event_read_allowed = {"family", "type", "symbol", "severity", "producer", "degraded", "include_non_production", "cursor", "limit"}
    event_read_choices = {
        "severity": {"low", "medium", "high", "critical"},
        "degraded": {"true", "false"},
    }
    if tokens[:2] == ["events", "recent"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"limit": 20},
            allowed=event_read_allowed,
            bool_flags={"include_non_production"},
            choices=event_read_choices,
        )
        if params is None:
            return None
        return _spec("/v1/events/recent", _string_true_flags(params, "include_non_production"))
    if tokens[:2] == ["events", "history"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"limit": 50},
            allowed=event_read_allowed,
            bool_flags={"include_non_production"},
            choices=event_read_choices,
        )
        if params is None:
            return None
        return _spec("/v1/events/history", _string_true_flags(params, "include_non_production"))
    if tokens[:3] == ["events", "receipts", "list"]:
        params = _parse_flags(
            tokens[3:],
            defaults={"limit": 50},
            allowed={"event_id", "consumer", "status", "limit", "include_non_production"},
            bool_flags={"include_non_production"},
            choices={"status": {"received", "processed", "rejected", "deferred"}},
        )
        if params is None:
            return None
        return _spec("/v1/events/receipts", _string_true_flags(params, "include_non_production"))
    if tokens[:2] == ["events", "export"]:
        params = _parse_flags(
            tokens[2:],
            defaults={"limit": 20},
            allowed={"format", "consumer", "family", "type", "symbol", "severity", "producer", "degraded", "include_non_production", "limit"},
            bool_flags={"include_non_production"},
            choices={
                "format": {"fx-event-detector"},
                "consumer": {"fx-event-detector", "event-feed-context", "shadow-trigger-path", "conductor-context-loader"},
                "severity": {"low", "medium", "high", "critical"},
                "degraded": {"true", "false"},
            },
        )
        params = _with_required(params, "format")
        if params is None:
            return None
        params = _bool_value(params, "degraded")
        if params is None:
            return None
        return _spec("/v1/events/export", method="POST", json_body=params, timeout=30.0)
    return None


def match_route(argv: Sequence[str]) -> RouteSpec | None:
    """Return a fast-path request spec for read-only CLI argv.

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

    if tokens[:2] == ["fx", "options-proxy"]:
        params = _with_required(
            _parse_flags(tokens[2:], defaults={}, allowed={"symbol"}),
            "symbol",
        )
        return None if params is None else _spec("/v1/fx/options-proxy", params)

    if tokens[:2] == ["fx", "positioning"]:
        params = _with_required(
            _parse_flags(tokens[2:], defaults={}, allowed={"symbol"}),
            "symbol",
        )
        return None if params is None else _spec("/v1/fx/positioning", params)

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

    if tokens[:2] == ["stocks", "optionability"]:
        params = _parse_flags(tokens[2:], defaults={"symbol": "AAPL"}, allowed={"symbol"})
        return None if params is None else _spec("/v1/stocks/optionability", params, auth_required=False, timeout=60.0)

    for matcher in (_match_macro, _match_options, _match_orderflow, _match_events, _match_crypto, _match_geopolitics, _match_polymarket, _match_alerts, _match_evidence):
        spec = matcher(tokens)
        if spec is not None:
            return spec

    return None
