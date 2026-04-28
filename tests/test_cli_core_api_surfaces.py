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
    calls: list[tuple[str, dict, dict | None]] = []

    def __init__(self, timeout=20.0):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.calls.append((url, headers or {}, params or {}))
        return _FakeResponse({"ok": True, "url": url, "params": params or {}})


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
    url, headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/evidence/feed"
    assert headers["Authorization"] == "Bearer ck_test"
    assert params == {"limit": 5, "assets": ["XAUUSD"]}


def test_alerts_dead_letter_command_hits_clean_tail_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["alerts", "dead-letter", "--limit", "3"])

    url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/alerts/dead-letter"
    assert params == {"limit": 3}


def test_context_fx_command_hits_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "fx", "--symbol", "XAUUSD", "--timeframe", "1h", "--count", "3"])

    url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/context/fx"
    assert params == {"symbol": "XAUUSD", "timeframe": "1h", "count": 3}


def test_context_gold_command_hits_gold_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "gold", "--symbol", "XAUUSD"])

    url, _headers, _params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/gold/context"


def test_context_stocks_command_hits_stocks_context_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["context", "stocks", "--symbol", "AAPL"])

    url, _headers, _params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/context"


def test_fx_quote_command_hits_currency_pair_quote_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "quote", "--symbol", "EURUSD"])

    url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/quote"
    assert params == {"symbol": "EURUSD"}


def test_fx_indicators_command_hits_currency_pair_indicators_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "indicators", "--symbol", "USDJPY", "--timeframe", "H1", "--bars", "50"])

    url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/indicators"
    assert params == {"symbol": "USDJPY", "timeframe": "H1", "bars": 50}


def test_package_version_matches_new_release():
    assert __version__ == "0.1.5"
