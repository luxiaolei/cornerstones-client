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


def _run(monkeypatch, capsys, argv, config=None):
    _FakeClient.calls = []
    monkeypatch.setattr(cli.httpx, "Client", _FakeClient)
    monkeypatch.setattr(cli, "load_config", lambda: config or {"api_base_url": "http://api.test", "api_key": "ck_test"})
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


def test_public_commands_do_not_require_saved_api_key(monkeypatch, capsys):
    config = {"api_base_url": "http://api.test", "api_key": None, "trial_token": "ctrial.secret", "trial_cookie": None}
    _run(monkeypatch, capsys, ["macro", "summary"], config=config)

    _method, url, headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/macro/summary"
    assert headers == {}
    assert params == {}


def test_fx_indicators_command_hits_currency_pair_indicators_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "indicators", "--symbol", "USDJPY", "--timeframe", "H1", "--bars", "50"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/indicators"
    assert params == {"symbol": "USDJPY", "timeframe": "H1", "bars": 50}


def test_fx_options_proxy_command_hits_options_proxy_data_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "options-proxy", "--symbol", "EURUSD"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/options-proxy"
    assert params == {"symbol": "EURUSD"}


def test_fx_positioning_command_hits_provider_availability_contract(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["fx", "positioning", "--symbol", "EURUSD"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/fx/positioning"
    assert params == {"symbol": "EURUSD"}


def test_stocks_filings_command_can_select_sec_provider(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["stocks", "filings", "--symbol", "AAPL", "--provider", "sec", "--form", "10-K", "--limit", "2"])

    _method, url, headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/filings"
    assert headers["Authorization"] == "Bearer ck_test"
    assert params == {"symbol": "AAPL", "provider": "sec", "form": "10-K", "limit": 2}


def test_stocks_facts_command_hits_sec_company_facts_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["stocks", "facts", "--symbol", "AAPL", "--period", "annual", "--limit", "4"])

    _method, url, headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/facts"
    assert headers["Authorization"] == "Bearer ck_test"
    assert params == {"symbol": "AAPL", "provider": "sec", "period": "annual", "limit": 4}


@pytest.mark.parametrize(
    ("argv", "route", "params"),
    [
        (["stocks", "transcripts", "--symbol", "AAPL", "--year", "2025", "--quarter", "4", "--limit", "1", "--include-text"], "/v1/stocks/transcripts", {"symbol": "AAPL", "year": 2025, "quarter": 4, "limit": 1, "include_text": True}),
        (["stocks", "analyst-estimates", "--symbol", "AAPL", "--period", "quarter", "--limit", "6", "--from", "2025-01-01", "--to", "2026-01-01"], "/v1/stocks/analyst-estimates", {"symbol": "AAPL", "period": "quarter", "limit": 6, "from": "2025-01-01", "to": "2026-01-01"}),
        (["stocks", "analyst-estimates", "--symbol", "AAPL", "--period", "ttm", "--limit", "6"], "/v1/stocks/analyst-estimates", {"symbol": "AAPL", "period": "ttm", "limit": 6}),
        (["stocks", "ratings", "--symbol", "AAPL", "--limit", "7", "--from", "2025-01-01", "--to", "2026-01-01"], "/v1/stocks/ratings", {"symbol": "AAPL", "limit": 7, "from": "2025-01-01", "to": "2026-01-01"}),
        (["stocks", "price-targets", "--symbol", "AAPL", "--limit", "8", "--from", "2025-01-01", "--to", "2026-01-01", "--include-consensus"], "/v1/stocks/price-targets", {"symbol": "AAPL", "limit": 8, "from": "2025-01-01", "to": "2026-01-01", "include_consensus": True}),
        (["stocks", "ratios", "--symbol", "AAPL", "--period", "ttm", "--limit", "5"], "/v1/stocks/ratios", {"symbol": "AAPL", "period": "ttm", "limit": 5}),
        (["stocks", "key-metrics", "--symbol", "AAPL", "--period", "annual", "--limit", "5"], "/v1/stocks/key-metrics", {"symbol": "AAPL", "period": "annual", "limit": 5}),
        (["stocks", "research-context", "--symbol", "AAPL", "--sections", "transcripts,analyst,valuation", "--limit-per-section", "2", "--include-explanations"], "/v1/stocks/research-context", {"symbol": "AAPL", "sections": "transcripts,analyst,valuation", "limit_per_section": 2, "include_explanations": True}),
    ],
)
def test_stock_research_commands_hit_authenticated_mvp_a_surfaces(monkeypatch, capsys, argv, route, params):
    _run(monkeypatch, capsys, argv)

    _method, url, headers, actual_params = _FakeClient.calls[-1]
    assert url == f"http://api.test{route}"
    assert headers["Authorization"] == "Bearer ck_test"
    assert actual_params == params


@pytest.mark.parametrize(
    ("argv", "route", "params"),
    [
        (["stocks", "transcripts", "--symbol", "AAPL"], "/v1/stocks/transcripts", {"symbol": "AAPL", "limit": 20}),
        (["stocks", "price-targets", "--symbol", "AAPL"], "/v1/stocks/price-targets", {"symbol": "AAPL", "limit": 20}),
        (["stocks", "research-context", "--symbol", "AAPL"], "/v1/stocks/research-context", {"symbol": "AAPL", "limit_per_section": 3}),
    ],
)
def test_stock_research_optional_bool_flags_omit_when_absent(monkeypatch, capsys, argv, route, params):
    _run(monkeypatch, capsys, argv)

    _method, url, _headers, actual_params = _FakeClient.calls[-1]
    assert url == f"http://api.test{route}"
    assert actual_params == params


def test_stock_research_help_is_provider_safe(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["cornerstones-client", "stocks", "research-context", "--help"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "research context" in output.lower()
    assert "provider" not in output.lower()


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
        "--yes",
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
    _run(monkeypatch, capsys, ["alerts", "delete", "--subscription-id", "sub_test", "--yes"] )

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
        "--yes",
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


def test_events_delete_deletes_customer_subscription(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["events", "delete", "--subscription-id", "evsub_test", "--yes"])

    method, url, _headers, body = _FakeClient.calls[-1]
    assert method == "DELETE"
    assert url == "http://api.test/v1/alerts/evsub_test"
    assert body is None


def test_subscription_mutations_require_yes(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _run(monkeypatch, capsys, [
            "alerts", "subscribe",
            "--asset", "XAUUSD",
            "--lane", "x_pressure",
            "--webhook-url", "https://client.example.com/alerts",
        ])
    assert _FakeClient.calls == []


def test_stocks_imbalance_window_command_hits_window_surface(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["stocks", "imbalance-window", "--symbol", "AAPL", "--exchange", "NYSE", "--window-minutes", "30"])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/stocks/imbalance-window"
    assert params == {"symbol": "AAPL", "exchange": "NYSE", "window_minutes": 30}


def test_package_version_matches_new_release():
    assert __version__ == "0.1.21"


def test_options_chain_command_maps_truth_surface_params(monkeypatch, capsys):
    _run(monkeypatch, capsys, [
        "options",
        "chain",
        "--symbol",
        "AAPL",
        "--max-expirations",
        "1",
        "--depth",
        "2",
        "--include",
        "quote,greeks,oi,volume,iv",
        "--preset",
        "compact",
    ])

    _method, url, _headers, params = _FakeClient.calls[-1]
    assert url == "http://api.test/v1/options/chain"
    assert params == {
        "symbol": "AAPL",
        "option_type": "both",
        "moneyness": "all",
        "depth": 2,
        "max_expirations": 1,
        "include": "quote,greeks,oi,volume,iv",
        "sort": "moneyness",
        "preset": "compact",
    }


def test_options_wall_and_analysis_accept_public_aliases(monkeypatch, capsys):
    _run(monkeypatch, capsys, ["options", "wall", "--symbol", "AAPL", "--threshold", "95"])
    _method, wall_url, _headers, wall_params = _FakeClient.calls[-1]
    assert wall_url == "http://api.test/v1/options/wall"
    assert wall_params == {"symbol": "AAPL", "threshold_percentile": 95.0}

    _run(monkeypatch, capsys, ["options", "analysis", "--symbol", "AAPL", "--expiration", "2026-05-15"])
    _method, analysis_url, _headers, analysis_params = _FakeClient.calls[-1]
    assert analysis_url == "http://api.test/v1/options/analysis"
    assert analysis_params == {"symbol": "AAPL", "expiration_date": "2026-05-15"}


def test_options_chain_help_documents_truth_identity_quality_and_no_submit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cornerstones-client", "options", "chain", "--help"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "truth envelope" in output
    assert "quote,greeks,oi,volume,iv" in output
    assert "does not imply trade permission" in output
