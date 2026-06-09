from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

from .config import DEFAULT_API_BASE_URL, DEFAULT_PORTAL_BASE_URL, load_config, save_config
from .public_safety import sanitize_public_payload


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ["secret", "token", "password", "authorization", "api_key"]):
                redacted[key] = "[REDACTED]" if item is not None else None
            else:
                redacted[key] = _redact_secrets(item)
        return redacted
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    return value


def _print(payload: dict[str, Any], *, redact: bool = False) -> None:
    safe_payload = sanitize_public_payload(payload)
    safe_payload = _redact_secrets(safe_payload) if redact else safe_payload
    print(json.dumps(safe_payload, indent=2, ensure_ascii=False))


def _fail(error: str, message: str, *, status_code: int | None = None) -> None:
    payload: dict[str, Any] = {"error": error, "message": message}
    if status_code is not None:
        payload["status_code"] = status_code
    _print(payload)
    raise SystemExit(1)


def build_headers(config: dict[str, Any], *, allow_trial: bool = False, require_api_key: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {}
    bearer = config.get("api_key")
    if not bearer and allow_trial and not require_api_key:
        bearer = config.get("trial_token")
    if require_api_key and not bearer:
        _fail("not_logged_in", "Run auth login with an issued API key first.")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if config.get("trial_cookie"):
        headers["Cookie"] = config["trial_cookie"]
    return headers


def _portal_base_url(config: dict[str, Any] | None = None) -> str:
    payload = config or load_config()
    return payload.get("portal_base_url", DEFAULT_PORTAL_BASE_URL).rstrip("/")


def _api_base_url(config: dict[str, Any] | None = None) -> str:
    payload = config or load_config()
    return payload.get("api_base_url", DEFAULT_API_BASE_URL).rstrip("/")


def _store_trial_state(config: dict[str, Any], response: httpx.Response) -> dict[str, Any]:
    set_cookie = response.headers.get("set-cookie")
    if set_cookie:
        config["trial_cookie"] = set_cookie.split(';', 1)[0]
    payload = response.json()
    token = payload.get("token", {}) if isinstance(payload, dict) else {}
    if isinstance(token, dict) and token.get("token"):
        config["trial_token"] = token["token"]
    save_config(config)
    return payload


def _ensure_trial_token(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("api_key") or config.get("trial_token"):
        return config
    with httpx.Client(timeout=15.0) as client:
        response = client.post(f"{_portal_base_url(config)}/api/trial/token", headers=build_headers(config, allow_trial=True))
    if response.status_code >= 400:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        _fail(payload.get("error", "trial_token_request_failed"), payload.get("message", response.text), status_code=response.status_code)
    _store_trial_state(config, response)
    return load_config()


def cmd_auth(args: argparse.Namespace) -> None:
    config = load_config()
    if args.auth_cmd == "set-base-url":
        config["portal_base_url"] = args.base_url.rstrip("/")
        save_config(config)
        _print({"saved": True, "portal_base_url": config["portal_base_url"]})
        return
    if args.auth_cmd == "set-api-base-url":
        config["api_base_url"] = args.api_base_url.rstrip("/")
        save_config(config)
        _print({"saved": True, "api_base_url": config["api_base_url"]})
        return
    if args.auth_cmd == "login":
        config["api_key"] = args.api_key
        save_config(config)
        _print({"logged_in": True, "api_base_url": config["api_base_url"]})
        return
    if args.auth_cmd == "logout":
        config["api_key"] = None
        save_config(config)
        _print({"logged_out": True})
        return
    if args.auth_cmd == "status":
        _print({
            "portal_base_url": config.get("portal_base_url"),
            "api_base_url": config.get("api_base_url"),
            "logged_in": bool(config.get("api_key")),
            "has_trial_cookie": bool(config.get("trial_cookie")),
            "has_trial_token": bool(config.get("trial_token")),
        })
        return


def cmd_trial(args: argparse.Namespace) -> None:
    config = load_config()
    if args.trial_cmd == "start":
        with httpx.Client(timeout=15.0) as client:
            response = client.post(f"{_portal_base_url(config)}/api/trial/start", headers=build_headers(config, allow_trial=True))
        if response.status_code >= 400:
            payload = response.json()
            _fail(payload.get("error", "trial_start_failed"), payload.get("message", response.text), status_code=response.status_code)
        payload = _store_trial_state(config, response)
        _print(payload)
        return
    if args.trial_cmd == "status":
        with httpx.Client(timeout=15.0) as client:
            response = client.get(f"{_portal_base_url(config)}/api/trial/status", headers=build_headers(config, allow_trial=True))
        if response.status_code >= 400:
            payload = response.json()
            _fail(payload.get("error", "trial_status_failed"), payload.get("message", response.text), status_code=response.status_code)
        _print(response.json())
        return
    if args.trial_cmd == "token":
        with httpx.Client(timeout=15.0) as client:
            response = client.post(f"{_portal_base_url(config)}/api/trial/token", headers=build_headers(config, allow_trial=True))
        if response.status_code >= 400:
            payload = response.json()
            _fail(payload.get("error", "trial_token_failed"), payload.get("message", response.text), status_code=response.status_code)
        payload = _store_trial_state(config, response)
        _print(payload)
        return


def _run_discovery_route(route: str) -> None:
    payload = _public_get(route, error="discovery_request_failed")
    _print(payload)


def _parse_response(response: httpx.Response, *, error: str) -> dict[str, Any]:
    if response.status_code >= 400:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        _fail(payload.get("error", error), payload.get("message", response.text), status_code=response.status_code)
    try:
        payload = response.json()
    except Exception:
        return {"content_type": response.headers.get("content-type"), "text": response.text}
    if isinstance(payload, dict):
        return payload
    return {"data": payload}


def _public_get(route: str, *, params: dict[str, Any] | list[tuple[str, Any]] | None = None, error: str = "request_failed") -> dict[str, Any]:
    config = load_config()
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{_api_base_url(config)}{route}",
            headers=build_headers(config),
            params=params,
        )
    return _parse_response(response, error=error)


def _authenticated_get(route: str, *, params: dict[str, Any] | list[tuple[str, Any]] | None = None, error: str = "request_failed") -> dict[str, Any]:
    config = load_config()
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{_api_base_url(config)}{route}",
            headers=build_headers(config, require_api_key=True),
            params=params,
        )
    return _parse_response(response, error=error)


def _authenticated_post(route: str, *, body: dict[str, Any], error: str = "request_failed") -> dict[str, Any]:
    config = load_config()
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{_api_base_url(config)}{route}",
            headers=build_headers(config, require_api_key=True),
            json=body,
        )
    return _parse_response(response, error=error)


def _authenticated_delete(route: str, *, error: str = "request_failed") -> dict[str, Any]:
    config = load_config()
    with httpx.Client(timeout=30.0) as client:
        response = client.delete(
            f"{_api_base_url(config)}{route}",
            headers=build_headers(config, require_api_key=True),
        )
    return _parse_response(response, error=error)


def _compact_params(raw: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in raw.items() if value is not None}


def _csv_values(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for raw in values or []:
        result.extend(part.strip() for part in raw.split(",") if part.strip())
    return result


def _require_yes(args: argparse.Namespace, action: str) -> None:
    if not getattr(args, "yes", False):
        _fail("confirmation_required", f"{action} changes customer subscription state. Re-run with --yes to confirm.")


def cmd_verify(_: argparse.Namespace) -> None:
    _print(_authenticated_get("/v1/status", error="verify_failed"))


def cmd_evidence(args: argparse.Namespace) -> None:
    if args.evidence_cmd == "feed":
        params = _compact_params({
            "limit": args.limit,
            "assets": args.asset or None,
            "types": args.type or None,
            "priority": args.priority,
        })
        _print(_authenticated_get("/v1/evidence/feed", params=params, error="evidence_feed_failed"))
        return


def _parse_kv_pairs(values: list[str] | None, *, name: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            _fail("invalid_argument", f"{name} must use KEY=VALUE format: {raw}")
        key, value = raw.split("=", 1)
        if not key:
            _fail("invalid_argument", f"{name} key cannot be empty")
        pairs[key] = value
    return pairs


def _delivery_from_args(args: argparse.Namespace) -> dict[str, Any]:
    signing_secret = getattr(args, "signing_secret", None)
    signing_secret_env = getattr(args, "signing_secret_env", None)
    if signing_secret_env:
        signing_secret = os.environ.get(signing_secret_env)
        if not signing_secret:
            _fail("missing_signing_secret", f"Environment variable {signing_secret_env} is not set.")
    delivery = _compact_params({
        "mode": getattr(args, "delivery_mode", "webhook"),
        "url": getattr(args, "webhook_url", None),
        "bridge_url": getattr(args, "bridge_url", None),
        "target": json.loads(args.target_json) if getattr(args, "target_json", None) else None,
        "headers": _parse_kv_pairs(getattr(args, "header", None), name="--header"),
        "signing_secret": signing_secret,
        "require_signing": getattr(args, "require_signing", False),
        "timeout_seconds": getattr(args, "timeout_seconds", None),
        "max_attempts": getattr(args, "max_attempts", None),
        "retry_backoff_seconds": getattr(args, "retry_backoff_seconds", None),
        "rate_limit_seconds": getattr(args, "rate_limit_seconds", None),
    })
    if delivery.get("mode") == "webhook" and not delivery.get("url"):
        _fail("missing_delivery_target", "--webhook-url is required for webhook delivery.")
    if delivery.get("mode") == "openclaw_bridge" and not delivery.get("bridge_url") and not delivery.get("target"):
        _fail("missing_delivery_target", "--bridge-url or --target-json is required for openclaw_bridge delivery.")
    return delivery


def _metadata_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return _compact_params({
        "name": getattr(args, "name", None),
        "created_by": getattr(args, "created_by", None),
        "notes": getattr(args, "notes", None),
    })


def cmd_alerts(args: argparse.Namespace) -> None:
    if args.alerts_cmd == "subscribe":
        _require_yes(args, "alerts subscribe")
        body = {
            "assets": _csv_values(args.asset),
            "lanes": _csv_values(args.lane),
            "filters": _compact_params({
                "min_priority": args.min_priority,
                "min_confidence": args.min_confidence,
                "cooldown_minutes": args.cooldown_minutes,
                "only_confirmed": args.only_confirmed,
                "max_active_alerts": args.max_active_alerts,
            }),
            "delivery": _delivery_from_args(args),
            "bootstrap": {"mode": args.bootstrap},
            "metadata": _metadata_from_args(args),
        }
        _print(_authenticated_post("/v1/alerts/subscribe", body=body, error="alerts_subscribe_failed"), redact=True)
        return
    if args.alerts_cmd == "delete":
        _require_yes(args, "alerts delete")
        _print(_authenticated_delete(f"/v1/alerts/{args.subscription_id}", error="alerts_delete_failed"), redact=True)
        return
    routes = {
        "metrics": "/v1/alerts/metrics",
        "recent": "/v1/alerts/recent",
        "dead-letter": "/v1/alerts/dead-letter",
        "list": "/v1/alerts",
        "history": "/v1/alerts/history",
        "security-status": "/v1/alerts/security-status",
        "show": f"/v1/alerts/{getattr(args, 'subscription_id', '')}",
    }
    params = _compact_params({
        "limit": getattr(args, "limit", None),
        "status": getattr(args, "status", None),
        "asset": getattr(args, "asset", None),
        "delivery_mode": getattr(args, "delivery_mode", None),
        "lane": getattr(args, "lane", None),
        "kind": getattr(args, "kind", None),
        "min_priority": getattr(args, "min_priority", None),
        "lifecycle": getattr(args, "lifecycle", None),
        "delivery_status": getattr(args, "delivery_status", None),
        "cursor": getattr(args, "cursor", None),
        "since_minutes": getattr(args, "since_minutes", None),
        "only_active": getattr(args, "only_active", None),
        "include_state": getattr(args, "include_state", None),
        "subscription_id": getattr(args, "subscription_id", None) if args.alerts_cmd == "security-status" else None,
    })
    _print(_authenticated_get(routes[args.alerts_cmd], params=params, error="alerts_request_failed"))


def cmd_fx(args: argparse.Namespace) -> None:
    if args.fx_cmd == "quote":
        params = _compact_params({"symbol": args.symbol})
        _print(_public_get("/v1/fx/quote", params=params, error="fx_quote_failed"))
        return
    if args.fx_cmd == "bars":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "count": args.count})
        _print(_public_get("/v1/fx/bars", params=params, error="fx_bars_failed"))
        return
    if args.fx_cmd == "indicators":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "bars": args.bars})
        _print(_authenticated_get("/v1/fx/indicators", params=params, error="fx_indicators_failed"))
        return
    if args.fx_cmd == "session":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "bars": args.bars})
        _print(_authenticated_get("/v1/fx/session", params=params, error="fx_session_failed"))
        return
    if args.fx_cmd == "levels":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "bars": args.bars})
        _print(_authenticated_get("/v1/fx/levels", params=params, error="fx_levels_failed"))
        return
    if args.fx_cmd == "opening-range":
        params = _compact_params({"symbol": args.symbol, "session": args.session, "minutes": args.minutes, "timeframe": args.timeframe, "bars": args.bars})
        _print(_authenticated_get("/v1/fx/opening-range", params=params, error="fx_opening_range_failed"))
        return
    if args.fx_cmd == "price-action":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "bars": args.bars})
        _print(_authenticated_get("/v1/fx/price-action", params=params, error="fx_price_action_failed"))
        return
    if args.fx_cmd == "volume-profile":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "basis": args.basis})
        _print(_authenticated_get("/v1/fx/volume-profile", params=params, error="fx_volume_profile_failed"))
        return
    if args.fx_cmd == "options-proxy":
        params = _compact_params({"symbol": args.symbol})
        _print(_authenticated_get("/v1/fx/options-proxy", params=params, error="fx_options_proxy_failed"))
        return
    if args.fx_cmd == "positioning":
        params = _compact_params({"symbol": args.symbol})
        _print(_authenticated_get("/v1/fx/positioning", params=params, error="fx_positioning_failed"))
        return


def cmd_context(args: argparse.Namespace) -> None:
    if args.context_cmd == "fx":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "count": args.count})
        _print(_authenticated_get("/v1/context/fx", params=params, error="context_fx_failed"))
        return
    if args.context_cmd == "gold":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "count": args.count})
        _print(_authenticated_get("/v1/gold/context", params=params, error="context_gold_failed"))
        return
    if args.context_cmd == "stocks":
        params = _compact_params({"symbol": args.symbol, "timeframe": args.timeframe, "count": args.count})
        _print(_authenticated_get("/v1/stocks/context", params=params, error="context_stocks_failed"))
        return


def cmd_orderflow(args: argparse.Namespace) -> None:
    routes = {
        "summary": "/v1/orderflow/summary",
        "context": "/v1/orderflow/context",
        "raw": "/v1/orderflow/raw",
        "historical": "/v1/orderflow/historical",
        "liquidity-metrics": "/v1/orderflow/liquidity-metrics",
    }
    params = _compact_params({"symbol": args.symbol})
    _print(_authenticated_get(routes[args.orderflow_cmd], params=params, error="orderflow_request_failed"))


def cmd_chart(args: argparse.Namespace) -> None:
    route = "/v1/fx/chart" if args.chart_cmd == "fx" else "/v1/stocks/chart"
    params = _compact_params({
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "bars": args.bars,
        "indicators": args.indicator or None,
        "template": args.template,
        "layout": args.layout,
        "layers": args.layer or None,
        "include": args.include or None,
        "chart_type": args.chart_type,
        "width": args.width,
        "height": args.height,
    })
    _print(_authenticated_get(route, params=params, error="chart_request_failed"))


def cmd_crypto(args: argparse.Namespace) -> None:
    routes = {name: f"/v1/crypto/{name}" for name in ["quote", "ticker", "bars", "indicators", "session", "depth", "trades"]}
    params = _compact_params({
        "symbol": args.symbol,
        "timeframe": getattr(args, "timeframe", None),
        "count": getattr(args, "count", None),
        "bars": getattr(args, "bars", None),
        "limit": getattr(args, "limit", None),
    })
    getter = _public_get if args.crypto_cmd in {"quote", "ticker", "bars"} else _authenticated_get
    _print(getter(routes[args.crypto_cmd], params=params, error="crypto_request_failed"))


def cmd_stocks(args: argparse.Namespace) -> None:
    routes = {
        "quote": "/v1/stocks/quote", "profile": "/v1/stocks/profile", "context": "/v1/stocks/context",
        "indicators": "/v1/stocks/indicators", "session": "/v1/stocks/session", "depth": "/v1/stocks/depth",
        "imbalance": "/v1/stocks/imbalance", "imbalance-window": "/v1/stocks/imbalance-window", "tick": "/v1/stocks/tick", "optionability": "/v1/stocks/optionability",
        "earnings": "/v1/stocks/earnings", "filings": "/v1/stocks/filings", "facts": "/v1/stocks/facts", "corporate-actions": "/v1/stocks/corporate-actions",
        "transcripts": "/v1/stocks/transcripts", "analyst-estimates": "/v1/stocks/analyst-estimates", "ratings": "/v1/stocks/ratings",
        "price-targets": "/v1/stocks/price-targets", "ratios": "/v1/stocks/ratios", "key-metrics": "/v1/stocks/key-metrics",
        "research-context": "/v1/stocks/research-context", "extended-hours": "/v1/stocks/extended-hours",
        "screener": "/v1/stocks/screener", "universe": "/v1/stocks/universe",
        "normalize-symbol": "/v1/stocks/symbols/normalize", "exchanges": "/v1/stocks/exchanges",
    }
    params = _compact_params({
        "symbol": getattr(args, "symbol", None), "timeframe": getattr(args, "timeframe", None), "bars": getattr(args, "bars", None),
        "bars_count": getattr(args, "bars_count", None), "num_rows": getattr(args, "num_rows", None), "exchange": getattr(args, "exchange", None),
        "window_minutes": getattr(args, "window_minutes", None), "tick_type": getattr(args, "tick_type", None), "num_ticks": getattr(args, "num_ticks", None), "from": getattr(args, "from_date", None),
        "to": getattr(args, "to_date", None), "status": getattr(args, "status", None), "provider": getattr(args, "provider", None), "form": getattr(args, "form", None), "period": getattr(args, "period", None),
        "type": getattr(args, "type", None), "limit": getattr(args, "limit", None), "preset": getattr(args, "preset", None),
        "year": getattr(args, "year", None), "quarter": getattr(args, "quarter", None), "include_text": getattr(args, "include_text", None),
        "include_consensus": getattr(args, "include_consensus", None), "sections": getattr(args, "sections", None),
        "limit_per_section": getattr(args, "limit_per_section", None), "include_explanations": getattr(args, "include_explanations", None),
        "session": getattr(args, "session", None),
        "marketCapMoreThan": getattr(args, "market_cap_more_than", None), "volumeMoreThan": getattr(args, "volume_more_than", None),
        "sector": getattr(args, "sector", None), "isEtf": getattr(args, "is_etf", None), "isFund": getattr(args, "is_fund", None),
        "isActivelyTrading": getattr(args, "is_actively_trading", None),
    })
    public_cmds = {"quote", "profile", "screener", "universe", "normalize-symbol", "exchanges", "alias-lookup"}
    if args.stocks_cmd == "alias-lookup":
        raw = getattr(args, "raw", "")
        _print(_public_get("/v1/stocks/alias-lookup", params={"raw": raw}, error="alias_lookup_failed"))
        return
    getter = _public_get if args.stocks_cmd in public_cmds else _authenticated_get
    _print(getter(routes[args.stocks_cmd], params=params, error="stocks_request_failed"))


def cmd_options(args: argparse.Namespace) -> None:
    routes = {"chain": "/v1/options/chain", "analysis": "/v1/options/analysis", "wall": "/v1/options/wall"}
    params = _compact_params({
        "symbol": args.symbol, "expiration_date": getattr(args, "expiration_date", None), "option_type": getattr(args, "option_type", None),
        "moneyness": getattr(args, "moneyness", None), "depth": getattr(args, "depth", None), "max_expirations": getattr(args, "max_expirations", None),
        "include": getattr(args, "include", None), "sort": getattr(args, "sort", None), "preset": getattr(args, "preset", None),
        "threshold_percentile": getattr(args, "threshold_percentile", None),
    })
    _print(_authenticated_get(routes[args.options_cmd], params=params, error="options_request_failed"))


def cmd_macro(args: argparse.Namespace) -> None:
    routes = {
        "summary": "/v1/macro/summary",
        "calendar": "/v1/macro/calendar",
        "series": "/v1/macro/series",
        "yields": "/v1/macro/yields",
        "event-window": "/v1/macro/event-window",
    }
    params = _compact_params({
        "name": getattr(args, "name", None), "from": getattr(args, "from_date", None), "to": getattr(args, "to_date", None),
        "from_date": getattr(args, "from_date", None), "to_date": getattr(args, "to_date", None), "country": getattr(args, "country", None),
        "currency": getattr(args, "currency", None), "importance": getattr(args, "importance", None), "category": getattr(args, "category", None),
        "symbol": getattr(args, "symbol", None), "lookback_minutes": getattr(args, "lookback_minutes", None), "lookahead_minutes": getattr(args, "lookahead_minutes", None),
    })
    getter = _public_get if args.macro_cmd in {"summary", "calendar"} else _authenticated_get
    _print(getter(routes[args.macro_cmd], params=params, error="macro_request_failed"))


def cmd_geopolitics(args: argparse.Namespace) -> None:
    routes = {
        "context": "/v1/geopolitics/context", "status": "/v1/geopolitics/status", "watchlist": "/v1/geopolitics/watchlist",
        "evidence": "/v1/geopolitics/evidence", "osint-feed": "/v1/geopolitics/osint-feed", "pizza-index": "/v1/geopolitics/pizza-index",
        "polymarket": "/v1/geopolitics/polymarket",
    }
    params = _compact_params({"limit": getattr(args, "limit", None), "min_priority": getattr(args, "min_priority", None), "keyword": getattr(args, "keyword", None)})
    _print(_authenticated_get(routes[args.geopolitics_cmd], params=params, error="geopolitics_request_failed"))


def cmd_polymarket(args: argparse.Namespace) -> None:
    routes = {"overview": "/v1/polymarket/overview", "context": "/v1/polymarket/context"}
    _print(_authenticated_get(routes[args.polymarket_cmd], error="polymarket_request_failed"))


def cmd_events(args: argparse.Namespace) -> None:
    if args.events_cmd == "subscribe":
        _require_yes(args, "events subscribe")
        body = {
            "filters": _compact_params({
                "family": args.family,
                "type": args.type,
                "symbol": args.symbol,
                "producer": args.producer,
                "min_severity": args.min_severity,
            }),
            "delivery": _delivery_from_args(args),
            "bootstrap": {"mode": args.bootstrap},
            "metadata": _metadata_from_args(args),
        }
        _print(_authenticated_post("/v1/events/subscribe", body=body, error="events_subscribe_failed"), redact=True)
        return
    if args.events_cmd == "delete":
        _require_yes(args, "events delete")
        _print(_authenticated_delete(f"/v1/alerts/{args.subscription_id}", error="events_delete_failed"), redact=True)
        return
    routes = {"recent": "/v1/events/recent", "history": "/v1/events/history", "receipts": "/v1/events/receipts"}
    params = _compact_params({
        "family": getattr(args, "family", None), "type": getattr(args, "type", None), "symbol": getattr(args, "symbol", None),
        "severity": getattr(args, "severity", None), "producer": getattr(args, "producer", None), "degraded": getattr(args, "degraded", None),
        "include_non_production": getattr(args, "include_non_production", None), "cursor": getattr(args, "cursor", None),
        "limit": getattr(args, "limit", None), "event_id": getattr(args, "event_id", None), "consumer": getattr(args, "consumer", None),
        "status": getattr(args, "status", None),
    })
    _print(_authenticated_get(routes[args.events_cmd], params=params, error="events_request_failed"))


def cmd_cross_asset(_: argparse.Namespace) -> None:
    _print(_authenticated_get("/v1/cross-asset/context", error="cross_asset_request_failed"))


def main() -> None:
    parser = argparse.ArgumentParser(prog="cornerstones-client", description="Public-safe Cornerstones client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    auth_parser = sub.add_parser("auth", help="Auth commands")
    auth_sub = auth_parser.add_subparsers(dest="auth_cmd", required=True)
    auth_status = auth_sub.add_parser("status")
    auth_status.set_defaults(func=cmd_auth)
    auth_login = auth_sub.add_parser("login")
    auth_login.add_argument("--api-key", required=True)
    auth_login.set_defaults(func=cmd_auth)
    auth_logout = auth_sub.add_parser("logout")
    auth_logout.set_defaults(func=cmd_auth)
    auth_base = auth_sub.add_parser("set-base-url")
    auth_base.add_argument("--base-url", required=True)
    auth_base.set_defaults(func=cmd_auth)
    auth_api_base = auth_sub.add_parser("set-api-base-url")
    auth_api_base.add_argument("--api-base-url", required=True)
    auth_api_base.set_defaults(func=cmd_auth)

    trial_parser = sub.add_parser("trial", help="Anonymous trial commands")
    trial_sub = trial_parser.add_subparsers(dest="trial_cmd", required=True)
    trial_start = trial_sub.add_parser("start")
    trial_start.set_defaults(func=cmd_trial)
    trial_status = trial_sub.add_parser("status")
    trial_status.set_defaults(func=cmd_trial)
    trial_token = trial_sub.add_parser("token")
    trial_token.set_defaults(func=cmd_trial)

    guide_parser = sub.add_parser("guide", help="Fetch public product discovery surface")
    guide_parser.set_defaults(func=lambda args: _run_discovery_route("/v1/features"))

    changelog_parser = sub.add_parser("changelog", help="Fetch admin-only product changelog using an issued admin API key")
    changelog_parser.set_defaults(func=lambda args: _print(_authenticated_get("/v1/changelog", error="changelog_request_failed")))

    evidence_parser = sub.add_parser("evidence", help="Read authenticated evidence surfaces")
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_cmd", required=True)
    evidence_feed = evidence_sub.add_parser("feed", help="Fetch live-backed evidence feed")
    evidence_feed.add_argument("--limit", type=int, default=10)
    evidence_feed.add_argument("--asset", action="append", help="Filter by asset; repeatable")
    evidence_feed.add_argument("--type", action="append", help="Filter by evidence type; repeatable")
    evidence_feed.add_argument("--priority")
    evidence_feed.set_defaults(func=cmd_evidence)

    def add_delivery_args(cmd: argparse.ArgumentParser) -> None:
        cmd.add_argument("--delivery-mode", choices=["webhook", "openclaw_bridge"], default="webhook")
        cmd.add_argument("--webhook-url")
        cmd.add_argument("--bridge-url")
        cmd.add_argument("--target-json", help="JSON object for bridge target metadata")
        cmd.add_argument("--header", action="append", help="Delivery header as KEY=VALUE; repeatable")
        cmd.add_argument("--signing-secret", help="Webhook signing secret; prefer --signing-secret-env")
        cmd.add_argument("--signing-secret-env", help="Read webhook signing secret from environment variable")
        cmd.add_argument("--require-signing", action="store_true")
        cmd.add_argument("--timeout-seconds", type=float)
        cmd.add_argument("--max-attempts", type=int)
        cmd.add_argument("--retry-backoff-seconds", type=int)
        cmd.add_argument("--rate-limit-seconds", type=float)
        cmd.add_argument("--name")
        cmd.add_argument("--created-by", default="client")
        cmd.add_argument("--notes")

    alerts_parser = sub.add_parser("alerts", help="Read and manage customer alert subscriptions")
    alerts_sub = alerts_parser.add_subparsers(dest="alerts_cmd", required=True)
    alerts_metrics = alerts_sub.add_parser("metrics", help="Fetch alert metrics")
    alerts_metrics.set_defaults(func=cmd_alerts)
    alerts_recent = alerts_sub.add_parser("recent", help="Fetch recent alert deliveries")
    alerts_recent.add_argument("--limit", type=int, default=10)
    alerts_recent.set_defaults(func=cmd_alerts)
    alerts_dead = alerts_sub.add_parser("dead-letter", help="Fetch alert dead-letter tail")
    alerts_dead.add_argument("--limit", type=int, default=10)
    alerts_dead.set_defaults(func=cmd_alerts)
    alerts_list = alerts_sub.add_parser("list", help="List alert subscriptions")
    alerts_list.add_argument("--status")
    alerts_list.add_argument("--asset")
    alerts_list.add_argument("--delivery-mode")
    alerts_list.set_defaults(func=cmd_alerts)
    alerts_history = alerts_sub.add_parser("history", help="Fetch alert history")
    for p in ["asset", "lane", "kind", "min-priority", "lifecycle", "delivery-status", "cursor"]:
        alerts_history.add_argument(f"--{p}")
    alerts_history.add_argument("--limit", type=int, default=50)
    alerts_history.set_defaults(func=cmd_alerts)
    alerts_security = alerts_sub.add_parser("security-status", help="Fetch alert subscription security status")
    alerts_security.add_argument("--subscription-id", required=True)
    alerts_security.set_defaults(func=cmd_alerts)
    alerts_show = alerts_sub.add_parser("show", help="Show alert subscription")
    alerts_show.add_argument("--subscription-id", required=True)
    alerts_show.set_defaults(func=cmd_alerts)
    alerts_subscribe = alerts_sub.add_parser("subscribe", help="Create a customer alert subscription")
    alerts_subscribe.add_argument("--asset", action="append", required=True, help="Asset/symbol; repeatable")
    alerts_subscribe.add_argument("--lane", action="append", required=True, choices=[
        "scheduled_macro", "macro_event_window", "earnings_upcoming", "earnings_released", "filing_detected",
        "corporate_action_upcoming", "x_pressure", "news_pressure", "cross_source_pressure",
    ])
    alerts_subscribe.add_argument("--min-priority", default="medium", choices=["low", "medium", "high", "critical"])
    alerts_subscribe.add_argument("--min-confidence", type=float, default=0.7)
    alerts_subscribe.add_argument("--cooldown-minutes", type=int, default=15)
    alerts_subscribe.add_argument("--only-confirmed", action="store_true")
    alerts_subscribe.add_argument("--max-active-alerts", type=int, default=20)
    alerts_subscribe.add_argument("--bootstrap", choices=["none", "snapshot", "evaluate_now"], default="snapshot")
    alerts_subscribe.add_argument("--yes", action="store_true", help="Confirm customer subscription creation")
    add_delivery_args(alerts_subscribe)
    alerts_subscribe.set_defaults(func=cmd_alerts)
    alerts_delete = alerts_sub.add_parser("delete", help="Delete a customer alert subscription")
    alerts_delete.add_argument("--subscription-id", required=True)
    alerts_delete.add_argument("--yes", action="store_true", help="Confirm customer subscription deletion")
    alerts_delete.set_defaults(func=cmd_alerts)

    fx_parser = sub.add_parser("fx", help="Read FX currency-pair surfaces: [Layer 1] market truth + [Layer 2] objective structure")
    fx_sub = fx_parser.add_subparsers(dest="fx_cmd", required=True)
    fx_quote = fx_sub.add_parser("quote", help="[Layer 1] Fetch latest FX/currency-pair quote")
    fx_quote.add_argument("--symbol", required=True, help="Currency pair or metal pair, e.g. EURUSD or XAUUSD")
    fx_quote.set_defaults(func=cmd_fx)
    fx_bars = fx_sub.add_parser("bars", help="[Layer 1] Fetch provider-backed FX/currency-pair OHLCV bars")
    fx_bars.add_argument("--symbol", required=True)
    fx_bars.add_argument("--timeframe", default="1h")
    fx_bars.add_argument("--count", "--bars", dest="count", type=int, default=10, help="Number of bars; --bars is Core-compatible alias")
    fx_bars.set_defaults(func=cmd_fx)
    fx_indicators = fx_sub.add_parser("indicators", help="[Layer 1] Fetch deterministic FX/currency-pair indicators")
    fx_indicators.add_argument("--symbol", required=True)
    fx_indicators.add_argument("--timeframe", default="H1")
    fx_indicators.add_argument("--bars", type=int, default=200)
    fx_indicators.set_defaults(func=cmd_fx)
    fx_session = fx_sub.add_parser("session", help="[Layer 1] Fetch deterministic FX/currency-pair session summary")
    fx_session.add_argument("--symbol", required=True)
    fx_session.add_argument("--timeframe", default="H1")
    fx_session.add_argument("--bars", type=int, default=200)
    fx_session.set_defaults(func=cmd_fx)
    fx_levels = fx_sub.add_parser(
        "levels",
        help="[Layer 2] Fetch objective intraday prior/current/session levels from recent bars",
        description="Layer 2 objective FX prior/current/session level evidence from recent bars. No trade signal, entry/exit, or trading recommendation.",
    )
    fx_levels.add_argument("--symbol", required=True)
    fx_levels.add_argument("--timeframe", default="5m")
    fx_levels.add_argument("--bars", type=int, default=600)
    fx_levels.set_defaults(func=cmd_fx)
    fx_opening_range = fx_sub.add_parser(
        "opening-range",
        help="[Layer 2] Fetch objective opening-range state; no trading recommendation",
        description="Layer 2 opening-range evidence. No trading recommendation.",
    )
    fx_opening_range.add_argument("--symbol", required=True)
    fx_opening_range.add_argument("--session", default="london", choices=["asia", "london", "new_york", "new-york"])
    fx_opening_range.add_argument("--minutes", type=int, default=30)
    fx_opening_range.add_argument("--timeframe", default="5m")
    fx_opening_range.add_argument("--bars", type=int, default=600)
    fx_opening_range.set_defaults(func=cmd_fx)
    fx_price_action = fx_sub.add_parser(
        "price-action",
        help="[Layer 2] Fetch objective price-action structure; no signal/recommendation fields",
        description="Layer 2 price-action structure. No signal/recommendation fields.",
    )
    fx_price_action.add_argument("--symbol", required=True)
    fx_price_action.add_argument("--timeframe", default="H1")
    fx_price_action.add_argument("--bars", type=int, default=120)
    fx_price_action.set_defaults(func=cmd_fx)
    fx_volume_profile = fx_sub.add_parser(
        "volume-profile",
        help="[Layer 2] Fetch XAUUSD GC futures orderflow proxy volume profile; not centralized spot volume",
        description="Fetch XAUUSD volume profile from GC futures orderflow proxy buckets. Use provenance, profile_quality, degraded, and fallback before consuming POC/VAH/VAL. No trading recommendation.",
    )
    fx_volume_profile.add_argument("--symbol", default="XAUUSD", help="Supported symbol: XAUUSD")
    fx_volume_profile.add_argument("--timeframe", default="15m", choices=["15m", "30m", "1h", "M15", "M30", "H1"], help="Aggregation window over GC proxy buckets")
    fx_volume_profile.add_argument("--basis", default="gc_futures", choices=["gc_futures", "gc_futures_orderflow_proxy"], help="Proxy basis; POC/VAH/VAL are conditional on profile_quality")
    fx_volume_profile.set_defaults(func=cmd_fx)
    fx_options_proxy = fx_sub.add_parser("options-proxy", help="[Layer 2] Fetch ETF options proxy data facts for an FX pair; downstream agents decide usage")
    fx_options_proxy.add_argument("--symbol", required=True)
    fx_options_proxy.set_defaults(func=cmd_fx)
    fx_positioning = fx_sub.add_parser("positioning", help="[Layer 2] Fetch FX positioning provider-availability contract")
    fx_positioning.add_argument("--symbol", required=True)
    fx_positioning.set_defaults(func=cmd_fx)

    context_parser = sub.add_parser("context", help="Read authenticated market context surfaces")
    context_sub = context_parser.add_subparsers(dest="context_cmd", required=True)
    context_fx = context_sub.add_parser("fx", help="Fetch FX context")
    context_fx.add_argument("--symbol", default="XAUUSD")
    context_fx.add_argument("--timeframe", default="1h")
    context_fx.add_argument("--count", type=int, default=5)
    context_fx.set_defaults(func=cmd_context)
    context_gold = context_sub.add_parser("gold", help="Fetch gold context")
    context_gold.add_argument("--symbol", default="XAUUSD")
    context_gold.add_argument("--timeframe", default="1h")
    context_gold.add_argument("--count", type=int, default=5)
    context_gold.set_defaults(func=cmd_context)
    context_stocks = context_sub.add_parser("stocks", help="Fetch stock context")
    context_stocks.add_argument("--symbol", default="AAPL")
    context_stocks.add_argument("--timeframe", default="1d")
    context_stocks.add_argument("--count", type=int, default=5)
    context_stocks.set_defaults(func=cmd_context)

    orderflow_parser = sub.add_parser("orderflow", help="Read authenticated order-flow data-contract surfaces")
    orderflow_sub = orderflow_parser.add_subparsers(dest="orderflow_cmd", required=True)
    for name, help_text in [
        ("summary", "Fetch order-flow data summary"),
        ("context", "Fetch order-flow data context"),
        ("raw", "Fetch raw/latest order-flow data payload"),
        ("historical", "Fetch historical order-flow data payload"),
        ("liquidity-metrics", "Fetch order-flow liquidity metrics data contract"),
    ]:
        orderflow_cmd = orderflow_sub.add_parser(name, help=help_text)
        orderflow_cmd.add_argument("--symbol", help="Instrument symbol, e.g. XAUUSD")
        orderflow_cmd.set_defaults(func=cmd_orderflow)

    chart_parser = sub.add_parser("chart", help="Render authenticated chart surfaces")
    chart_sub = chart_parser.add_subparsers(dest="chart_cmd", required=True)
    for name, default_symbol, default_timeframe, help_text in [
        ("fx", "XAUUSD", "H1", "Render an FX/currency-pair chart"),
        ("stocks", "AAPL", "1d", "Render a stock chart"),
    ]:
        chart_cmd = chart_sub.add_parser(name, help=help_text)
        chart_cmd.add_argument("--symbol", default=default_symbol)
        chart_cmd.add_argument("--timeframe", default=default_timeframe)
        chart_cmd.add_argument("--bars", type=int, default=200)
        chart_cmd.add_argument("--indicator", action="append", help="Indicator overlay; repeatable")
        chart_cmd.add_argument("--template")
        chart_cmd.add_argument("--layout")
        chart_cmd.add_argument("--layer", action="append", help="Chart layer; repeatable")
        chart_cmd.add_argument("--include", action="append", help="Extra chart component; repeatable")
        chart_cmd.add_argument("--chart-type")
        chart_cmd.add_argument("--width", type=int, default=1600)
        chart_cmd.add_argument("--height", type=int, default=1000)
        chart_cmd.set_defaults(func=cmd_chart)

    crypto_parser = sub.add_parser("crypto", help="Read authenticated crypto market surfaces")
    crypto_sub = crypto_parser.add_subparsers(dest="crypto_cmd", required=True)
    for name in ["quote", "ticker"]:
        c = crypto_sub.add_parser(name)
        c.add_argument("--symbol", required=True)
        c.set_defaults(func=cmd_crypto)
    for name in ["bars", "indicators", "session"]:
        c = crypto_sub.add_parser(name)
        c.add_argument("--symbol", required=True)
        c.add_argument("--timeframe", default="1h")
        if name == "bars":
            c.add_argument("--count", type=int, default=100)
        else:
            c.add_argument("--bars", type=int, default=200)
        c.set_defaults(func=cmd_crypto)
    for name, default_limit in [("depth", 50), ("trades", 100)]:
        c = crypto_sub.add_parser(name)
        c.add_argument("--symbol", required=True)
        c.add_argument("--limit", type=int, default=default_limit)
        c.set_defaults(func=cmd_crypto)

    stocks_parser = sub.add_parser("stocks", help="Read authenticated stock market surfaces")
    stocks_sub = stocks_parser.add_subparsers(dest="stocks_cmd", required=True)
    for name in ["quote", "profile", "optionability"]:
        c = stocks_sub.add_parser(name)
        c.add_argument("--symbol", required=True, help="Stock symbol, e.g. AAPL, 600519.SS, 000001.SZ")
        c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("normalize-symbol", help="Normalize stock symbol (600519.SH -> 600519.SS; .BJ unsupported in current phase)")
    c.add_argument("--symbol", required=True)
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("alias-lookup", help="Resolve company name / raw ticker → tradeable symbol (e.g. 'SK HYNIX' → 000660.KS)")
    c.add_argument("--raw", required=True, help="Raw company name or ticker to resolve, e.g. 'SK HYNIX', 'APPL', '3105'")
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("exchanges", help="List stock exchange support metadata, including A-share SHH/SHZ")
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("context"); c.add_argument("--symbol", required=True, help="Stock symbol, e.g. AAPL, 600519.SS, 000001.SZ"); c.add_argument("--bars-count", type=int, default=5); c.set_defaults(func=cmd_stocks)
    for name in ["indicators", "session"]:
        c = stocks_sub.add_parser(name); c.add_argument("--symbol", required=True); c.add_argument("--timeframe", default="1d"); c.add_argument("--bars", type=int, default=200 if name == "indicators" else 252); c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("depth"); c.add_argument("--symbol", required=True); c.add_argument("--num-rows", type=int, default=5); c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("imbalance", help="Fetch auction imbalance snapshot")
    c.add_argument("--symbol", required=True); c.add_argument("--exchange", default="NYSE"); c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("imbalance-window", help="Fetch auction imbalance rolling window facts")
    c.add_argument("--symbol", required=True); c.add_argument("--exchange", default="NYSE"); c.add_argument("--window-minutes", type=int, default=30); c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("tick"); c.add_argument("--symbol", required=True); c.add_argument("--tick-type", default="Last"); c.add_argument("--num-ticks", type=int, default=100); c.set_defaults(func=cmd_stocks)
    for name in ["earnings", "filings", "corporate-actions"]:
        c = stocks_sub.add_parser(name); c.add_argument("--symbol", required=True); c.add_argument("--from", dest="from_date"); c.add_argument("--to", dest="to_date")
        if name == "earnings": c.add_argument("--status")
        if name == "filings": c.add_argument("--provider", default="fmp", choices=["fmp", "sec", "sec_edgar"]); c.add_argument("--form"); c.add_argument("--limit", type=int, default=20)
        if name == "corporate-actions": c.add_argument("--type", default="all")
        c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("facts", help="Fetch compact SEC EDGAR official company facts; requires configured core SEC user-agent for live data")
    c.add_argument("--symbol", required=True)
    c.add_argument("--provider", default="sec", choices=["sec", "sec_edgar"])
    c.add_argument("--period", choices=["annual", "fy", "quarterly", "quarter", "q1", "q2", "q3", "q4"])
    c.add_argument("--limit", type=int, default=20)
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("transcripts", help="Fetch earnings call transcripts")
    c.add_argument("--symbol", required=True)
    c.add_argument("--year", type=int)
    c.add_argument("--quarter", type=int)
    c.add_argument("--limit", type=int, default=20)
    c.add_argument("--include-text", action=argparse.BooleanOptionalAction, default=None)
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("analyst-estimates", help="Fetch analyst estimate rows")
    c.add_argument("--symbol", required=True)
    c.add_argument("--period", default="annual", choices=["annual", "quarter", "ttm"])
    c.add_argument("--limit", type=int, default=20)
    c.add_argument("--from", dest="from_date")
    c.add_argument("--to", dest="to_date")
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("ratings", help="Fetch analyst rating rows")
    c.add_argument("--symbol", required=True)
    c.add_argument("--limit", type=int, default=20)
    c.add_argument("--from", dest="from_date")
    c.add_argument("--to", dest="to_date")
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("price-targets", help="Fetch price target rows and optional consensus")
    c.add_argument("--symbol", required=True)
    c.add_argument("--limit", type=int, default=20)
    c.add_argument("--from", dest="from_date")
    c.add_argument("--to", dest="to_date")
    c.add_argument("--include-consensus", action=argparse.BooleanOptionalAction, default=None)
    c.set_defaults(func=cmd_stocks)
    for research_name, help_text in [("ratios", "Fetch valuation ratio rows"), ("key-metrics", "Fetch key metric rows")]:
        c = stocks_sub.add_parser(research_name, help=help_text)
        c.add_argument("--symbol", required=True)
        c.add_argument("--period", default="annual", choices=["annual", "quarter", "ttm"])
        c.add_argument("--limit", type=int, default=20)
        c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("research-context", help="Fetch stock research context", description="Fetch stock research context from neutral evidence inputs.")
    c.add_argument("--symbol", required=True)
    c.add_argument("--sections")
    c.add_argument("--limit-per-section", type=int, default=3)
    c.add_argument("--include-explanations", action=argparse.BooleanOptionalAction, default=None)
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("extended-hours", help="Fetch combined extended-hours quote/trade overlay with observed_session")
    c.add_argument("--symbol", required=True)
    c.add_argument("--session", default="extended", choices=["extended", "pre-market", "after-hours"], help="Requested session label; provider scope is combined extended-hours")
    c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("screener"); c.add_argument("--market-cap-more-than"); c.add_argument("--volume-more-than"); c.add_argument("--exchange", help="Exchange filter, e.g. NASDAQ, NYSE, SHH, SHZ"); c.add_argument("--sector"); c.add_argument("--is-etf"); c.add_argument("--is-fund"); c.add_argument("--is-actively-trading"); c.add_argument("--limit", type=int, default=25); c.set_defaults(func=cmd_stocks)
    c = stocks_sub.add_parser("universe"); c.add_argument("--preset", default="us-stocks-liquid", help="Universe preset, e.g. us-stocks-liquid or china-a-shares-largecap"); c.add_argument("--limit", type=int, default=25); c.set_defaults(func=cmd_stocks)

    options_parser = sub.add_parser("options", help="Read authenticated stock options surfaces")
    options_sub = options_parser.add_subparsers(dest="options_cmd", required=True)
    c = options_sub.add_parser(
        "chain",
        help="Fetch read-only option chain truth envelope (identity + quote/Greeks/liquidity metadata)",
        description="Read-only option chain truth envelope. Surfaces sec_type=OPT, underlying_type, quote/Greeks/liquidity quality metadata. No BAG/ComboLeg/whatIf/submit/cancel/risk/reconciliation.",
    )
    c.add_argument("--symbol", required=True, help="Underlying symbol, e.g. AAPL or SPX")
    c.add_argument("--expiration", "--expiration-date", dest="expiration_date", help="Optional expiration date YYYY-MM-DD")
    c.add_argument("--option-type", default="both", choices=["call", "put", "both"], help="Filter contracts by side")
    c.add_argument("--moneyness", default="all", choices=["all", "itm", "atm", "otm"], help="Filter by moneyness against reference price")
    c.add_argument("--depth", type=int, help="Max strikes per expiration")
    c.add_argument("--max-expirations", type=int, help="Max expirations to return")
    c.add_argument("--include", help="Projection fields: quote,greeks,oi,volume,iv")
    c.add_argument("--sort", default="moneyness", choices=["moneyness", "strike", "oi", "volume"], help="Output sort order")
    c.add_argument("--preset", default="compact", choices=["compact", "expanded"], help="Snapshot preset; does not imply trade permission")
    c.set_defaults(func=cmd_options)
    c = options_sub.add_parser("analysis", help="Fetch read-only option analysis with chain quality disclosure")
    c.add_argument("--symbol", required=True, help="Underlying symbol, e.g. AAPL")
    c.add_argument("--expiration", "--expiration-date", dest="expiration_date", help="Optional expiration date YYYY-MM-DD")
    c.set_defaults(func=cmd_options)
    c = options_sub.add_parser("wall", help="Fetch read-only put/call wall analysis; no broker submit")
    c.add_argument("--symbol", required=True, help="Underlying symbol, e.g. AAPL")
    c.add_argument("--expiration", "--expiration-date", dest="expiration_date", help="Optional expiration date YYYY-MM-DD")
    c.add_argument("--threshold", "--threshold-percentile", dest="threshold_percentile", type=float, default=90.0, help="Open-interest wall percentile threshold")
    c.set_defaults(func=cmd_options)

    macro_parser = sub.add_parser("macro", help="Read macro surfaces: [Layer 3] intelligence/economic context")
    macro_sub = macro_parser.add_subparsers(dest="macro_cmd", required=True)
    c = macro_sub.add_parser("summary", help="[Layer 3] Fetch macro summary")
    c.set_defaults(func=cmd_macro)
    c = macro_sub.add_parser("yields", help="[Layer 3] Fetch treasury yield curve")
    c.set_defaults(func=cmd_macro)
    c = macro_sub.add_parser("series", help="[Layer 3] Fetch exact-semantic macro series")
    c.add_argument("--name", required=True)
    c.set_defaults(func=cmd_macro)
    c = macro_sub.add_parser("calendar", help="[Layer 3] Fetch FMP-backed macro calendar with normalized filters")
    c.add_argument("--from", dest="from_date"); c.add_argument("--to", dest="to_date"); c.add_argument("--country"); c.add_argument("--currency"); c.add_argument("--importance", choices=["low", "medium", "high"]); c.add_argument("--category"); c.set_defaults(func=cmd_macro)
    c = macro_sub.add_parser(
        "event-window",
        help="[Layer 3] Fetch objective scheduled macro event window; no execution recommendation",
        description="Fetch objective scheduled macro event window evidence. Response uses event_window_state, blackout_suggestion, provenance, degraded, and fallback; no trading recommendation.",
    )
    c.add_argument("--symbol", required=True)
    c.add_argument("--currency")
    c.add_argument("--lookback-minutes", type=int, default=60)
    c.add_argument("--lookahead-minutes", type=int, default=240)
    c.add_argument("--importance", choices=["low", "medium", "high"])
    c.set_defaults(func=cmd_macro)

    geopolitics_parser = sub.add_parser("geopolitics", help="Read authenticated geopolitics/OSINT surfaces")
    geopolitics_sub = geopolitics_parser.add_subparsers(dest="geopolitics_cmd", required=True)
    for name in ["context", "status", "watchlist", "pizza-index"]:
        c = geopolitics_sub.add_parser(name); c.set_defaults(func=cmd_geopolitics)
    c = geopolitics_sub.add_parser("evidence"); c.add_argument("--min-priority", default="low"); c.set_defaults(func=cmd_geopolitics)
    c = geopolitics_sub.add_parser("osint-feed"); c.add_argument("--limit", type=int, default=20); c.add_argument("--min-priority", default="low"); c.set_defaults(func=cmd_geopolitics)
    c = geopolitics_sub.add_parser("polymarket"); c.add_argument("--limit", type=int, default=10); c.add_argument("--keyword"); c.set_defaults(func=cmd_geopolitics)

    polymarket_parser = sub.add_parser("polymarket", help="Read authenticated Polymarket surfaces")
    polymarket_sub = polymarket_parser.add_subparsers(dest="polymarket_cmd", required=True)
    for name in ["overview", "context"]:
        c = polymarket_sub.add_parser(name); c.set_defaults(func=cmd_polymarket)

    events_parser = sub.add_parser("events", help="Read authenticated event bus surfaces")
    events_sub = events_parser.add_subparsers(dest="events_cmd", required=True)
    for name in ["recent", "history"]:
        c = events_sub.add_parser(name)
        for p in ["family", "type", "symbol", "severity", "producer", "degraded", "cursor"]: c.add_argument(f"--{p}")
        c.add_argument("--include-non-production", action="store_true")
        c.add_argument("--limit", type=int, default=20 if name == "recent" else 50)
        c.set_defaults(func=cmd_events)
    c = events_sub.add_parser("receipts"); c.add_argument("--event-id"); c.add_argument("--consumer"); c.add_argument("--status"); c.add_argument("--include-non-production", action="store_true"); c.add_argument("--limit", type=int, default=50); c.set_defaults(func=cmd_events)
    c = events_sub.add_parser("subscribe", help="Create a customer event subscription")
    c.add_argument("--symbol", required=True)
    c.add_argument("--family")
    c.add_argument("--type")
    c.add_argument("--producer", default="alerts_current_source")
    c.add_argument("--min-severity", default="medium", choices=["low", "medium", "high", "critical"])
    c.add_argument("--bootstrap", choices=["none", "snapshot", "recent"], default="snapshot")
    c.add_argument("--yes", action="store_true", help="Confirm customer subscription creation")
    add_delivery_args(c)
    c.set_defaults(func=cmd_events)
    c = events_sub.add_parser("delete", help="Delete a customer event subscription")
    c.add_argument("--subscription-id", required=True)
    c.add_argument("--yes", action="store_true", help="Confirm customer subscription deletion")
    c.set_defaults(func=cmd_events)

    cross_asset_parser = sub.add_parser("cross-asset", help="Read authenticated cross-asset context")
    cross_asset_parser.set_defaults(func=cmd_cross_asset)

    verify_parser = sub.add_parser("verify", help="Verify a real authenticated API key against /v1/status")
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
