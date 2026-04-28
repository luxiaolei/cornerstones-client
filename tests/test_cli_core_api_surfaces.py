from __future__ import annotations

import json

import pytest

from cornerstones_client import __version__
from cornerstones_client import cli


class _FakeResponse:
    status_code = 200
    text = "{}"

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    calls: list[tuple[str, str, dict, dict | None]] = []

    def __init__(self, timeout=20.0):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.calls.append(("GET", url, headers or {}, params or {}))
        return _FakeResponse({"ok": True, "url": url, "params": params or {}})

    def post(self, url, headers=None, json=None):
        self.calls.append(("POST", url, headers or {}, json or {}))
        return _FakeResponse({"ok": True, "url": url, "body": json or {}})

    def delete(self, url, headers=None):
        self.calls.append(("DELETE", url, headers or {}, None))
        return _FakeResponse({"ok": True, "url": url, "deleted": True})


def _run(monkeypatch, capsys, argv):
    _FakeClient.calls = []
    monkeypatch.setattr(cli.httpx, "Client", _FakeClient)
    monkeypatch.setattr(cli, "load_config", lambda: {"api_base_url": "http://api.test", "api_key": "ck_test"})
    monkeypatch.setattr("sys.argv", ["cornerstones-client", *argv])
    cli.main()
    return json.loads(capsys.readouterr().out)


def test_evidence_feed_command_hits_live_backed_feed(monkeypatch, capsys):
    payload = _run(monkeypatch, capsys, ["evidence", "feed", "--limit", "5", "--asset", "XAUUSD"])

    assert payload["ok"] is True
    _method, url, headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/evidence/feed"
    assert headers["Authorization"] == "Bearer ck_test"
    assert params == {"limit": 5, "assets": ["XAUUSD"]}


def test_alerts_dead_letter_command_hits_clean_tail_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["alerts", "dead-letter", "--limit", "3"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/alerts/dead-letter"
    assert params == {"limit": 3}


def test_context_fx_command_hits_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "fx", "--symbol", "XAUUSD", "--timeframe", "1h", "--count", "3"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/context/fx"
    assert params == {"symbol": "XAUUSD", "timeframe": "1h", "count": 3}


def test_context_gold_command_hits_gold_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "gold", "--symbol", "XAUUSD"])

    _method, url, _headers, _params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/gold/context"


def test_context_stocks_command_hits_stocks_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "stocks", "--symbol", "AAPL"])

    _method, url, _headers, _params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/context"


def test_fx_quote_command_hits_currency_pair_quote_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "quote", "--symbol", "EURUSD"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/quote"
    assert params == {"symbol": "EURUSD"}


def test_fx_indicators_command_hits_currency_pair_indicators_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "indicators", "--symbol", "USDJPY", "--timeframe", "H1", "--bars", "50"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/indicators"
    assert params == {"symbol": "USDJPY", "timeframe": "H1", "bars": 50}


def test_orderflow_summary_command_hits_orderflow_summary_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["orderflow", "summary", "--symbol", "XAUUSD"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/orderflow/summary"
    assert params == {"symbol": "XAUUSD"}


def test_orderflow_liquidity_metrics_command_hits_liquidity_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["orderflow", "liquidity-metrics", "--symbol", "XAUUSD"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/orderflow/liquidity-metrics"
    assert params == {"symbol": "XAUUSD"}


def test_chart_fx_command_hits_fx_chart_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, [
        "chart", "fx", "--symbol", "XAUUSD", "--timeframe", "H1", "--bars", "120", "--indicator", "rsi", "--layer", "orderflow"
    ])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/chart"
    assert params == {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "bars": 120,
        "indicators": ["rsi"],
        "layers": ["orderflow"],
        "width": 1600,
        "height": 1000,
    }


def test_chart_stocks_command_hits_stocks_chart_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["chart", "stocks", "--symbol", "AAPL", "--timeframe", "1d", "--bars", "80"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/chart"
    assert params == {"symbol": "AAPL", "timeframe": "1d", "bars": 80, "width": 1600, "height": 1000}


def test_alerts_subscribe_posts_customer_subscription(monkeypatch, capsys):
    payload = _run(monkeypatch, capsys, [
        "alerts", "subscribe",
        "--asset", "XAUUSD",
        "--asset", "EURUSD",
        "--lane", "macro_event_window",
        "--lane", "x_pressure",
        "--webhook-url", "https://client.example.com/alerts",
        "--header", "X-Test=yes",
        "--signing-secret", "secret-value",
        "--require-signing",
        "--name", "xau-alerts",
    ])

    method, url, headers, body = _FakeClient.calls[-1]
    assert payload["body"]["delivery"]["signing_secret"] == "[REDACTED]"
    assert method == "POST"
    assert url == "http://api.test/v1/alerts/subscribe"
    assert headers["Authorization"] == "Bearer ck_test"
    assert body["assets"] == ["XAUUSD", "EURUSD"]
    assert body["lanes"] == ["macro_event_window", "x_pressure"]
    assert body["delivery"]["url"] == "https://client.example.com/alerts"
    assert body["delivery"]["headers"] == {"X-Test": "yes"}
    assert body["delivery"]["require_signing"] is True
    assert body["metadata"]["name"] == "xau-alerts"


def test_alerts_delete_deletes_customer_subscription(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["alerts", "delete", "--subscription-id", "sub_test"] )

    method, url, _headers, body = _FakeClient.calls[-1]
    assert method == "DELETE"
    assert url == "http://api.test/v1/alerts/sub_test"
    assert body is None


def test_events_subscribe_posts_customer_subscription(monkeypatch, capsys):
    _run(monkeypatch, capsys, [
        "events", "subscribe",
        "--symbol", "XAUUSD",
        "--family", "scheduled_macro",
        "--min-severity", "high",
        "--webhook-url", "https://client.example.com/events",
        "--bootstrap", "recent",
    ])

    method, url, _headers, body = _FakeClient.calls[-1]
    assert method == "POST"
    assert url == "http://api.test/v1/events/subscribe"
    assert body["filters"] == {
        "family": "scheduled_macro",
        "symbol": "XAUUSD",
        "producer": "alerts_current_source",
        "min_severity": "high",
    }
    assert body["delivery"]["url"] == "https://client.example.com/events"
    assert body["bootstrap"] == {"mode": "recent"}


def test_package_version_matches_new_release():
    assert __version__ == "0.1.8"
