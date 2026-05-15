from __future__ import annotations

import io
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError

import pytest


def test_fastpath_route_mapping_covers_phase1_surfaces():
    from cornerstones_client.fastpath.routes import match_route

    cases = [
        (["health", "status"], "GET", "/health", {}, False, None),
        (["context", "fx", "--symbol", "EURUSD", "--timeframe", "M15", "--count", "3"], "GET", "/v1/context/fx", {"symbol": "EURUSD", "timeframe": "M15", "count": 3}, True, None),
        (["fx", "quote", "--symbol", "EURUSD"], "GET", "/v1/fx/quote", {"symbol": "EURUSD"}, True, None),
        (["fx", "bars", "--symbol", "EURUSD", "--timeframe", "M15"], "GET", "/v1/fx/bars", {"symbol": "EURUSD", "timeframe": "M15"}, True, None),
        (["fx", "indicators", "--symbol", "EURUSD", "--timeframe", "M15", "--bars", "200"], "GET", "/v1/fx/indicators", {"symbol": "EURUSD", "timeframe": "M15", "bars": 200}, True, None),
        (["fx", "session", "--symbol", "EURUSD", "--timeframe", "M15", "--bars", "200"], "GET", "/v1/fx/session", {"symbol": "EURUSD", "timeframe": "M15", "bars": 200}, True, None),
        (["fx", "options-proxy", "--symbol", "EURUSD"], "GET", "/v1/fx/options-proxy", {"symbol": "EURUSD"}, True, None),
        (["fx", "positioning", "--symbol", "EURUSD"], "GET", "/v1/fx/positioning", {"symbol": "EURUSD"}, True, None),
        (["cross-asset", "context"], "GET", "/v1/cross-asset/context", {}, True, None),
        (["stocks", "quote", "--symbol", "GLD"], "GET", "/v1/stocks/quote", {"symbol": "GLD"}, True, None),
        (["stocks", "context", "--symbol", "GLD", "--bars-count", "3"], "GET", "/v1/stocks/context", {"symbol": "GLD", "bars_count": 3}, True, None),
        (["stocks", "filings", "--symbol", "AAPL", "--provider", "sec", "--form", "10-K", "--limit", "2"], "GET", "/v1/stocks/filings", {"symbol": "AAPL", "provider": "sec", "form": "10-K", "limit": 2}, True, None),
        (["stocks", "facts", "--symbol", "AAPL", "--period", "annual", "--limit", "4"], "GET", "/v1/stocks/facts", {"symbol": "AAPL", "provider": "sec", "period": "annual", "limit": 4}, True, None),
        (["stocks", "transcripts", "--symbol", "AAPL", "--year", "2025", "--quarter", "4", "--limit", "1", "--include-text"], "GET", "/v1/stocks/transcripts", {"symbol": "AAPL", "year": 2025, "quarter": 4, "limit": 1, "include_text": "true"}, True, None),
        (["stocks", "analyst-estimates", "--symbol", "AAPL", "--period", "quarter", "--limit", "6", "--from", "2025-01-01", "--to", "2026-01-01"], "GET", "/v1/stocks/analyst-estimates", {"symbol": "AAPL", "period": "quarter", "limit": 6, "from": "2025-01-01", "to": "2026-01-01"}, True, None),
        (["stocks", "ratings", "--symbol", "AAPL", "--limit", "7", "--from", "2025-01-01", "--to", "2026-01-01"], "GET", "/v1/stocks/ratings", {"symbol": "AAPL", "limit": 7, "from": "2025-01-01", "to": "2026-01-01"}, True, None),
        (["stocks", "price-targets", "--symbol", "AAPL", "--limit", "8", "--from", "2025-01-01", "--to", "2026-01-01", "--include-consensus"], "GET", "/v1/stocks/price-targets", {"symbol": "AAPL", "limit": 8, "from": "2025-01-01", "to": "2026-01-01", "include_consensus": "true"}, True, None),
        (["stocks", "transcripts", "--symbol", "AAPL"], "GET", "/v1/stocks/transcripts", {"symbol": "AAPL", "limit": 20}, True, None),
        (["stocks", "price-targets", "--symbol", "AAPL"], "GET", "/v1/stocks/price-targets", {"symbol": "AAPL", "limit": 20}, True, None),
        (["stocks", "ratios", "--symbol", "AAPL", "--period", "ttm", "--limit", "5"], "GET", "/v1/stocks/ratios", {"symbol": "AAPL", "period": "ttm", "limit": 5}, True, None),
        (["stocks", "key-metrics", "--symbol", "AAPL", "--period", "annual", "--limit", "5"], "GET", "/v1/stocks/key-metrics", {"symbol": "AAPL", "period": "annual", "limit": 5}, True, None),
        (["stocks", "research-context", "--symbol", "AAPL", "--sections", "transcripts,analyst,valuation", "--limit-per-section", "2", "--include-explanations"], "GET", "/v1/stocks/research-context", {"symbol": "AAPL", "sections": "transcripts,analyst,valuation", "limit_per_section": 2, "include_explanations": "true"}, True, None),
        (["context", "gold"], "GET", "/v1/context/gold", {}, True, None),
        (["gold", "context"], "GET", "/v1/gold/context", {}, True, None),
        (["macro", "yields"], "GET", "/v1/macro/yields", {}, True, None),
        (["macro", "summary"], "GET", "/v1/macro/summary", {}, True, None),
        (["macro", "series", "--name", "us10y_real"], "GET", "/v1/macro/series", {"name": "us10y_real"}, True, None),
        (["macro", "calendar", "--from", "2026-05-07", "--to", "2026-05-14", "--country", "US"], "GET", "/v1/macro/calendar", {"from": "2026-05-07", "to": "2026-05-14", "country": "US"}, True, None),
        (["stocks", "optionability", "--symbol", "AAPL"], "GET", "/v1/stocks/optionability", {"symbol": "AAPL"}, False, None),
        (["options", "chain", "--symbol", "AAPL", "--max-expirations", "1", "--depth", "2", "--preset", "compact", "--include", "quote,greeks,oi,volume,iv"], "GET", "/v1/options/chain", {"symbol": "AAPL", "option_type": "both", "moneyness": "all", "sort": "moneyness", "preset": "compact", "max_expirations": 1, "depth": 2, "include": "quote,greeks,oi,volume,iv"}, True, None),
        (["options", "chain", "--symbol", "AAPL", "--expiration-date", "2026-05-15"], "GET", "/v1/options/chain", {"symbol": "AAPL", "option_type": "both", "moneyness": "all", "sort": "moneyness", "preset": "compact", "expiration_date": "2026-05-15"}, True, None),
        (["options", "wall", "--symbol", "AAPL", "--threshold", "90"], "GET", "/v1/options/wall", {"symbol": "AAPL", "threshold_percentile": 90.0}, True, None),
        (["options", "wall", "--symbol", "AAPL", "--threshold-percentile", "95"], "GET", "/v1/options/wall", {"symbol": "AAPL", "threshold_percentile": 95.0}, True, None),
        (["options", "analysis", "--symbol", "AAPL", "--expiration", "2026-05-15"], "GET", "/v1/options/analysis", {"symbol": "AAPL", "expiration_date": "2026-05-15"}, True, None),
        (["orderflow", "raw", "-s", "XAUUSD"], "GET", "/v1/orderflow/raw", {"symbol": "XAUUSD"}, True, None),
        (["orderflow", "summary", "--symbol", "XAUUSD"], "GET", "/v1/orderflow/summary", {"symbol": "XAUUSD"}, True, None),
        (["orderflow", "context", "--symbol", "XAUUSD"], "GET", "/v1/orderflow/context", {"symbol": "XAUUSD"}, True, None),
        (["orderflow", "historical", "--symbol", "XAUUSD"], "GET", "/v1/orderflow/historical", {"symbol": "XAUUSD"}, True, None),
        (["orderflow", "liquidity-metrics", "--symbol", "XAUUSD"], "GET", "/v1/orderflow/liquidity-metrics", {"symbol": "XAUUSD"}, True, None),
        (["events", "recent", "--symbol", "XAUUSD", "--include-non-production", "--limit", "5"], "GET", "/v1/events/recent", {"limit": 5, "symbol": "XAUUSD", "include_non_production": "true"}, True, None),
        (["events", "history", "--family", "scheduled_macro", "--degraded", "false"], "GET", "/v1/events/history", {"limit": 50, "family": "scheduled_macro", "degraded": "false"}, True, None),
        (["events", "receipts", "list", "--consumer", "fx-event-detector", "--limit", "10"], "GET", "/v1/events/receipts", {"limit": 10, "consumer": "fx-event-detector"}, True, None),
        (["events", "export", "--format", "fx-event-detector", "--consumer", "fx-event-detector", "--degraded", "false", "--include-non-production"], "POST", "/v1/events/export", {}, True, {"format": "fx-event-detector", "limit": 20, "consumer": "fx-event-detector", "degraded": False, "include_non_production": True}),
        (["crypto", "quote"], "GET", "/v1/crypto/quote", {"symbol": "BTCUSDT"}, True, None),
        (["crypto", "bars", "--symbol", "ETHUSDT", "--timeframe", "1h", "--count", "12"], "GET", "/v1/crypto/bars", {"symbol": "ETHUSDT", "timeframe": "1h", "count": 12}, True, None),
        (["crypto", "depth", "--symbol", "BTCUSDT", "--limit", "20"], "GET", "/v1/crypto/depth", {"symbol": "BTCUSDT", "limit": 20}, True, None),
        (["crypto", "trades", "--symbol", "BTCUSDT", "--limit", "20"], "GET", "/v1/crypto/trades", {"symbol": "BTCUSDT", "limit": 20}, True, None),
        (["crypto", "ticker", "--symbol", "BTCUSDT"], "GET", "/v1/crypto/ticker", {"symbol": "BTCUSDT"}, True, None),
        (["crypto", "session", "--symbol", "BTCUSDT", "--timeframe", "1h", "--bars", "50"], "GET", "/v1/crypto/session", {"symbol": "BTCUSDT", "timeframe": "1h", "bars": 50}, True, None),
        (["crypto", "indicators", "--symbol", "BTCUSDT", "--timeframe", "1h", "--bars", "50"], "GET", "/v1/crypto/indicators", {"symbol": "BTCUSDT", "timeframe": "1h", "bars": 50}, True, None),
        (["geopolitics"], "GET", "/v1/geopolitics/status", {}, True, None),
        (["geopolitics", "context"], "GET", "/v1/geopolitics/context", {}, True, None),
        (["geopolitics", "osint-feed", "--limit", "5", "--priority", "high", "--region", "US"], "GET", "/v1/geopolitics/osint-feed", {"limit": 5, "priority": "high", "region": "US"}, True, None),
        (["geopolitics", "pizza-index"], "GET", "/v1/geopolitics/pizza-index", {}, True, None),
        (["geopolitics", "polymarket", "--limit", "5", "--keyword", "war"], "GET", "/v1/geopolitics/polymarket", {"limit": 5, "keyword": "war"}, True, None),
        (["geopolitics", "evidence", "--min-priority", "critical"], "GET", "/v1/geopolitics/evidence", {"min_priority": "critical"}, True, None),
        (["polymarket", "overview"], "GET", "/v1/polymarket/overview", {}, True, None),
        (["polymarket", "context"], "GET", "/v1/polymarket/context", {}, True, None),
        (["alerts", "recent", "--asset", "XAUUSD", "--lane", "scheduled_macro", "--since-minutes", "30", "--only-active", "--limit", "5"], "GET", "/v1/alerts/recent", {"since_minutes": 30, "limit": 5, "only_active": "true", "asset": "XAUUSD", "lane": "scheduled_macro"}, True, None),
        (["alerts", "history", "--asset", "XAUUSD", "--delivery-status", "delivered", "--limit", "5"], "GET", "/v1/alerts/history", {"limit": 5, "asset": "XAUUSD", "delivery_status": "delivered"}, True, None),
        (["alerts", "metrics"], "GET", "/v1/alerts/metrics", {}, True, None),
        (["alerts", "metrics", "--hide-state"], "GET", "/v1/alerts/metrics", {"include_state": "false"}, True, None),
        (["evidence", "feed"], "GET", "/v1/evidence/feed", {"types": ["signal", "alert", "opportunity", "anomaly"], "min_priority": "low", "limit": 50, "raw_evidence_only": "true"}, True, None),
        (["evidence", "feed", "--min-priority", "high", "--min-confidence", "0.5", "--limit", "10"], "GET", "/v1/evidence/feed", {"types": ["signal", "alert", "opportunity", "anomaly"], "min_priority": "high", "limit": 10, "raw_evidence_only": "true", "min_confidence": 0.5}, True, None),
    ]

    for case in cases:
        argv, method, path, params, auth_required, json_body = case
        spec = match_route(argv)
        assert spec is not None, argv
        assert spec.method == method
        assert spec.path == path
        assert spec.params == params
        assert spec.auth_required is auth_required
        assert getattr(spec, "json_body", None) == json_body


def test_fastpath_route_mapping_rejects_invalid_choices_and_core_only_aliases():
    from cornerstones_client.fastpath.routes import match_route

    invalid_cases = [
        ["macro", "series", "--name", "bad"],
        ["macro", "calendar", "--importance", "urgent"],
        ["options", "chain", "--option-type", "bogus"],
        ["options", "chain", "--moneyness", "near"],
        ["options", "chain", "--sort", "bad"],
        ["options", "chain", "--preset", "wide"],
        ["fx", "quote", "-s", "EURUSD"],
        ["stocks", "quote", "-s", "AAPL"],
        ["options", "chain", "-s", "AAPL"],
        ["events", "recent", "-s", "XAUUSD"],
        ["stocks", "context", "--bars_count", "3"],
        ["options", "chain", "--option_type", "call"],
        ["options", "chain", "--max_expirations", "1"],
        ["events", "recent", "--include_non_production"],
        ["macro", "calendar", "--from_date", "2026-05-07"],
        ["events", "recent", "--severity", "urgent"],
        ["events", "recent", "--degraded", "maybe"],
        ["events", "receipts", "list", "--status", "done"],
        ["events", "export", "--format", "bad"],
        ["events", "export", "--format", "fx-event-detector", "--consumer", "bad"],
        ["fx", "quote", "--symbol", "--bad-flag"],
        ["fx", "quote", "--symbol", "-s"],
        ["fx", "options-proxy", "--symbol", "--bad-flag"],
        ["fx", "positioning", "--symbol", "-s"],
        ["stocks", "filings", "--provider", "bad"],
        ["stocks", "facts", "--period", "decade"],
        ["stocks", "analyst-estimates", "--period", "monthly"],
        ["stocks", "ratios", "--period", "decade"],
        ["stocks", "key-metrics", "--period", "decade"],
        ["stocks", "research-context", "--limit_per_section", "2"],
        ["crypto", "quote", "--symbol", "--bad-flag"],
        ["alerts", "recent", "--asset", "--bad-flag"],
        ["crypto", "quote", "-s", "BTCUSDT"],
        ["crypto", "bars", "--count", "bad"],
        ["geopolitics", "osint-feed", "--priority", "urgent"],
        ["geopolitics", "evidence", "--min-priority", "urgent"],
        ["polymarket", "context", "--limit", "5"],
        ["alerts", "recent", "--lane", "bad"],
        ["alerts", "recent", "--only_active"],
        ["alerts", "history", "--delivery-status", "bad"],
        ["alerts", "metrics", "--include-state", "true"],
        ["evidence", "feed", "--min-priority", "urgent"],
        ["evidence", "feed", "--types", "signal", "alert"],
    ]

    for argv in invalid_cases:
        assert match_route(argv) is None, argv


def test_fastpath_error_payloads_redact_url_body_and_message():
    from cornerstones_client.fastpath.http import FastPathHTTPError, FastPathRequestFailed

    http_payload = FastPathHTTPError(
        401,
        "https://user-red:pass-red@example.test/path?token=tok-red&symbol=EURUSD#secret=frag-red",
        "api_key=body-red",
    ).payload()
    request_payload = FastPathRequestFailed(
        "https://u-red:p-red@example.test/path?password=query-red&symbol=EURUSD#opaque-fragment-value",
        "authorization=msg-red",
    ).payload()
    text = json.dumps({"http": http_payload, "request": request_payload})

    for leaked in [
        "user-red",
        "pass-red",
        "tok-red",
        "body-red",
        "frag-red",
        "u-red",
        "p-red",
        "query-red",
        "msg-red",
        "opaque-fragment-value",
    ]:
        assert leaked not in text
    assert "[REDACTED]" in text
    assert "symbol=EURUSD" in text


def test_fastpath_request_json_does_not_forward_auth_on_redirect():
    from cornerstones_client.fastpath.config import RuntimeConfig
    from cornerstones_client.fastpath.http import FastPathHTTPError, request_json
    from cornerstones_client.fastpath.routes import RouteSpec

    target_authorizations: list[str | None] = []

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            target_authorizations.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        def log_message(self, format, *args):
            return

    target = HTTPServer(("127.0.0.1", 0), TargetHandler)

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/target")
            self.end_headers()

        def log_message(self, format, *args):
            return

    redirector = HTTPServer(("127.0.0.1", 0), RedirectHandler)
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (target, redirector)]
    for thread in threads:
        thread.start()

    try:
        with pytest.raises(FastPathHTTPError) as exc_info:
            request_json(
                RouteSpec("GET", "/redirect", {}, auth_required=True, timeout=2.0),
                RuntimeConfig(f"http://127.0.0.1:{redirector.server_port}", "env"),
            )
    finally:
        redirector.shutdown()
        target.shutdown()
        redirector.server_close()
        target.server_close()

    assert exc_info.value.status_code == 302
    assert target_authorizations == []


def test_fastpath_route_rejects_admin_and_unknown_flags():
    from cornerstones_client.fastpath.routes import match_route

    assert match_route(["admin", "status"]) is None
    assert match_route(["alerts", "replay", "--limit", "1"]) is None
    assert match_route(["fx", "quote", "--symbol", "EURUSD", "--mutate"]) is None


def test_fastpath_config_keeps_core_credentials_with_core_base(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    core_dir = tmp_path / "cornerstones"
    client_dir = tmp_path / "cornerstones-client"
    core_dir.mkdir(parents=True)
    client_dir.mkdir(parents=True)
    (core_dir / "credentials.json").write_text(json.dumps({"api_key": "core"}))
    (client_dir / "config.json").write_text(json.dumps({"api_base_url": "https://client.example", "api_key": "client"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_FASTPATH_DEFAULT_BASE_URL", "http://192.168.0.21:8100")

    config = load_runtime_config()

    assert config.base_url == "http://192.168.0.21:8100"
    assert config.api_key == "core"
    assert config.source == "core"


def test_fastpath_config_prefers_stored_core_credentials_over_stale_env(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    core_dir = tmp_path / "cornerstones"
    core_dir.mkdir(parents=True)
    (core_dir / "credentials.json").write_text(json.dumps({"api_key": "core"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_API_KEY", "stale")

    config = load_runtime_config()

    assert config.api_key == "core"
    assert config.source == "core"


def test_fastpath_config_env_base_does_not_send_stored_bearer(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    core_dir = tmp_path / "cornerstones"
    core_dir.mkdir(parents=True)
    (core_dir / "credentials.json").write_text(json.dumps({"api_key": "core"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")

    config = load_runtime_config()

    assert config.base_url == "http://env-api.test"
    assert config.api_key is None
    assert config.source == "env"


def test_fastpath_config_env_base_uses_only_explicit_env_key(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    client_dir = tmp_path / "cornerstones-client"
    client_dir.mkdir(parents=True)
    (client_dir / "config.json").write_text(json.dumps({"api_base_url": "https://client.example", "api_key": "client"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config = load_runtime_config()

    assert config.base_url == "https://client.example"
    assert config.api_key == "client"
    assert config.source == "client"


def test_fastpath_config_uses_client_trial_token_for_trial_reads(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    client_dir = tmp_path / "cornerstones-client"
    client_dir.mkdir(parents=True)
    (client_dir / "config.json").write_text(json.dumps({"api_base_url": "https://client.example", "trial_token": "ctrial_client"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config = load_runtime_config()

    assert config.base_url == "https://client.example"
    assert config.api_key == "ctrial_client"
    assert config.source == "client"


def test_fastpath_config_env_base_is_explicit_override(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")
    monkeypatch.setenv("CORNERSTONES_API_KEY", "env")

    config = load_runtime_config()

    assert config.base_url == "http://env-api.test"
    assert config.api_key == "env"
    assert config.source == "env"


def test_fastpath_request_json_sends_post_json_body(monkeypatch):
    from cornerstones_client.fastpath import http as fast_http
    from cornerstones_client.fastpath.config import RuntimeConfig
    from cornerstones_client.fastpath.http import request_json
    from cornerstones_client.fastpath.routes import RouteSpec

    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def getcode(self):
            return 200

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        calls.append(
            {
                "method": request.get_method(),
                "url": request.full_url,
                "content_type": request.get_header("Content-type"),
                "auth": request.get_header("Authorization"),
                "data": request.data.decode("utf-8"),
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(fast_http, "urlopen", fake_urlopen)

    payload = request_json(
        RouteSpec("POST", "/v1/events/export", {}, auth_required=True, timeout=7.0, json_body={"format": "fx-event-detector"}),
        RuntimeConfig("http://api.test", "env-key", source="env"),
    )

    assert payload == {"ok": True}
    assert calls == [
        {
            "method": "POST",
            "url": "http://api.test/v1/events/export",
            "content_type": "application/json",
            "auth": "Bearer env-key",
            "data": '{"format":"fx-event-detector"}',
            "timeout": 7.0,
        }
    ]


def test_fastpath_request_json_sends_optional_auth_and_falls_back_without_key(monkeypatch):
    from cornerstones_client.fastpath import http as fast_http
    from cornerstones_client.fastpath.config import RuntimeConfig
    from cornerstones_client.fastpath.http import FastPathFallback, request_json
    from cornerstones_client.fastpath.routes import RouteSpec

    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def getcode(self):
            return 200

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        calls.append(request.get_header("Authorization"))
        return FakeResponse()

    monkeypatch.setattr(fast_http, "urlopen", fake_urlopen)
    assert request_json(
        RouteSpec("GET", "/v1/stocks/optionability", {"symbol": "AAPL"}, auth_required=False),
        RuntimeConfig("http://api.test", "env-key", source="env"),
    ) == {"ok": True}
    assert calls == ["Bearer env-key"]

    def fake_forbidden(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", hdrs=None, fp=io.BytesIO(b"forbidden"))

    monkeypatch.setattr(fast_http, "urlopen", fake_forbidden)
    with pytest.raises(FastPathFallback):
        request_json(
            RouteSpec("GET", "/v1/stocks/optionability", {"symbol": "AAPL"}, auth_required=False),
            RuntimeConfig("http://api.test", None, source="core_default"),
        )


def test_fastpath_runner_uses_core_config_and_credentials(monkeypatch, tmp_path, capsys):
    from cornerstones_client.fastpath import http as fast_http
    from cornerstones_client.fastpath.runner import run

    config_dir = tmp_path / "cornerstones"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(json.dumps({"base_url": "http://api.test"}))
    (config_dir / "credentials.json").write_text(json.dumps({"api_key": "test"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    calls: list[tuple[str, str, str | None]] = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def getcode(self):
            return 200

        def read(self):
            return b'{"provenance":"mt5","message":"MT5 realtime quote"}'

    def fake_urlopen(request, timeout):
        calls.append((request.get_method(), request.full_url, request.get_header("Authorization")))
        return FakeResponse()

    monkeypatch.setattr(fast_http, "urlopen", fake_urlopen)

    assert run(["fx", "quote", "--symbol", "EURUSD"]) == 0
    assert calls == [("GET", "http://api.test/v1/fx/quote?symbol=EURUSD", "Bearer test")]
    assert json.loads(capsys.readouterr().out) == {
        "provenance": "cornerstones_market_data",
        "message": "cornerstones_market_data realtime quote",
    }


def test_fastpath_runner_blocks_env_source_fallback_for_auth_route(monkeypatch, tmp_path, capsys):
    from cornerstones_client.fastpath import runner
    from cornerstones_client.fastpath.http import FastPathFallback

    core_dir = tmp_path / "cornerstones"
    core_dir.mkdir(parents=True)
    (core_dir / "credentials.json").write_text(json.dumps({"api_key": "core"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")
    monkeypatch.setenv("CORNERSTONES_API_KEY", "env")

    seen_sources: list[str] = []

    def fake_request_json(spec, config):
        seen_sources.append(config.source)
        raise FastPathFallback("server route unavailable")

    monkeypatch.setattr(runner, "request_json", fake_request_json)

    assert runner.run(["fx", "quote", "--symbol", "EURUSD"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "fastpath_unavailable"
    assert seen_sources == ["env"]


def test_fastpath_runner_blocks_env_source_fallback_for_optional_v1_route(monkeypatch, tmp_path, capsys):
    from cornerstones_client.fastpath import runner
    from cornerstones_client.fastpath.http import FastPathFallback

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")

    def fake_request_json(spec, config):
        assert spec.auth_required is False
        assert spec.path == "/v1/stocks/optionability"
        assert config.source == "env"
        raise FastPathFallback("optional auth route unavailable")

    monkeypatch.setattr(runner, "request_json", fake_request_json)

    assert runner.run(["stocks", "optionability", "--symbol", "AAPL"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "fastpath_unavailable"


def test_fastpath_runner_blocks_env_source_unexpected_failure_for_auth_route(monkeypatch, tmp_path, capsys):
    from cornerstones_client.fastpath import runner

    core_dir = tmp_path / "cornerstones"
    core_dir.mkdir(parents=True)
    (core_dir / "credentials.json").write_text(json.dumps({"api_key": "core"}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")
    monkeypatch.setenv("CORNERSTONES_API_KEY", "env")

    def fake_request_json(spec, config):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(runner, "request_json", fake_request_json)

    assert runner.run(["fx", "quote", "--symbol", "EURUSD"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "fastpath_unavailable"
    assert "simulated timeout" not in json.dumps(payload)


def test_fastpath_runner_returns_none_for_unsupported_without_output(capsys):
    from cornerstones_client.fastpath.runner import run

    assert run(["auth", "login", "--api-key", "secret"]) is None
    assert capsys.readouterr().out == ""


def test_fastpath_runner_handles_missing_auth_without_http(monkeypatch, tmp_path, capsys):
    from cornerstones_client.fastpath import http as fast_http
    from cornerstones_client.fastpath.runner import run

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("HTTP should not run without credentials")

    monkeypatch.setattr(fast_http, "urlopen", fail_urlopen)

    assert run(["fx", "quote", "--symbol", "EURUSD"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "not_logged_in"
    assert "api_key" not in json.dumps(payload).lower()


def test_fastpath_import_has_no_heavy_cornerstones_modules():
    for name in list(sys.modules):
        if name.startswith(("cornerstones.domains", "cornerstones.api", "playwright", "ib_insync")):
            sys.modules.pop(name, None)

    import cornerstones_client.fastpath.runner  # noqa: F401

    loaded = [
        name
        for name in sys.modules
        if name.startswith(("cornerstones.domains", "cornerstones.api", "playwright", "ib_insync"))
    ]
    assert loaded == []
