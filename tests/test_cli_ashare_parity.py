from __future__ import annotations

import json

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


def _run(monkeypatch, capsys, argv):
    _FakeClient.calls = []
    monkeypatch.setattr(cli.httpx, "Client", _FakeClient)
    monkeypatch.setattr(cli, "load_config", lambda: {"api_base_url": "http://api.test", "api_key": "ck_test"})
    monkeypatch.setattr("sys.argv", ["cornerstones-client", *argv])
    cli.main()
    return json.loads(capsys.readouterr().out)


def test_client_stocks_ashare_quote_profile_context_parity(monkeypatch, capsys):
    commands = [
        (["stocks", "quote", "--symbol", "600519.SS"], "/v1/stocks/quote", {"symbol": "600519.SS"}),
        (["stocks", "profile", "--symbol", "000001.SZ"], "/v1/stocks/profile", {"symbol": "000001.SZ"}),
        (["stocks", "context", "--symbol", "600519.SS", "--bars-count", "5"], "/v1/stocks/context", {"symbol": "600519.SS", "bars_count": 5}),
        (["stocks", "indicators", "--symbol", "600519.SS", "--timeframe", "1d", "--bars", "200"], "/v1/stocks/indicators", {"symbol": "600519.SS", "timeframe": "1d", "bars": 200}),
        (["stocks", "session", "--symbol", "600519.SS", "--timeframe", "1d", "--bars", "252"], "/v1/stocks/session", {"symbol": "600519.SS", "timeframe": "1d", "bars": 252}),
    ]
    for argv, route, params in commands:
        _run(monkeypatch, capsys, argv)
        _method, url, headers, got_params = _FakeClient.calls[-1]
        assert url == f"http://api.test{route}"
        assert headers["Authorization"] == "Bearer ck_test"
        assert got_params == params


def test_client_stocks_ashare_screener_universe_helpers_parity(monkeypatch, capsys):
    commands = [
        (["stocks", "screener", "--exchange", "SHH", "--limit", "25"], "/v1/stocks/screener", {"exchange": "SHH", "limit": 25}),
        (["stocks", "screener", "--exchange", "SHZ", "--limit", "25"], "/v1/stocks/screener", {"exchange": "SHZ", "limit": 25}),
        (["stocks", "universe", "--preset", "china-a-shares-largecap", "--limit", "25"], "/v1/stocks/universe", {"preset": "china-a-shares-largecap", "limit": 25}),
        (["stocks", "normalize-symbol", "--symbol", "600519.SH"], "/v1/stocks/symbols/normalize", {"symbol": "600519.SH"}),
        (["stocks", "exchanges"], "/v1/stocks/exchanges", {}),
        (["chart", "stocks", "--symbol", "600519.SS", "--timeframe", "1d", "--bars", "120"], "/v1/stocks/chart", {"symbol": "600519.SS", "timeframe": "1d", "bars": 120, "width": 1600, "height": 1000}),
    ]
    for argv, route, params in commands:
        _run(monkeypatch, capsys, argv)
        _method, url, headers, got_params = _FakeClient.calls[-1]
        assert url == f"http://api.test{route}"
        assert headers["Authorization"] == "Bearer ck_test"
        assert got_params == params
