from __future__ import annotations

import json

import pytest

from cornerstones_client.cli import build_headers, main
from cornerstones_client.public_safety import sanitize_public_payload


def test_build_headers_includes_cookie_and_trial_bearer_only_when_allowed():
    config = {
        "api_key": None,
        "trial_token": "ctrial_trial.secret",
        "trial_cookie": "cornerstones_trial_session=abc",
    }
    headers = build_headers(config, allow_trial=True)
    assert headers["Authorization"] == "Bearer ctrial_trial.secret"
    assert headers["Cookie"] == "cornerstones_trial_session=abc"


def test_build_headers_does_not_use_trial_token_for_api_key_required_reads():
    config = {
        "api_key": None,
        "trial_token": "ctrial_trial.secret",
        "trial_cookie": None,
    }

    with pytest.raises(SystemExit):
        build_headers(config, allow_trial=True, require_api_key=True)


def test_build_headers_uses_api_key_for_api_key_required_reads():
    config = {
        "api_key": "csk_live_secret",
        "trial_token": "ctrial_trial.secret",
        "trial_cookie": None,
    }

    headers = build_headers(config, allow_trial=True, require_api_key=True)

    assert headers["Authorization"] == "Bearer csk_live_secret"


def test_cli_help_renders_public_safe_description(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cornerstones-client", "--help"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "Public-safe Cornerstones client" in output
    assert "auth" in output
    assert "trial" in output
    assert "verify" in output


def test_public_payload_sanitizer_hides_upstream_provider_labels():
    payload = {
        "provenance": "mt5+fmp+fmp+fmp+adanos",
        "message": "Multi-provider gold context [MT5/FMP/Adanos]",
        "fallback": {"from_provider": "okx", "to_provider": "bybit", "note": "OKX timeout"},
        "option_contract": {"fallback": "ib_options_quote_missing", "chain_fallback": "ib_options_quotes_missing", "partial_reason": "ib_options_quotes_partial", "empty_fallback": "ib_options_empty"},
        "providers": {"mt5": {"ready": True}, "fmp": {"ready": True}},
        "orderflow": {"provider": "rithmic", "provenance": "cornerstones+rithmic:stream"},
        "chart": {"engine": "tradingview_widget_local", "exchange_resolved": "OANDA"},
    }

    sanitized = sanitize_public_payload(payload)
    serialized = json.dumps(sanitized)

    assert sanitized["provenance"] == "cornerstones_gold_context"
    assert sanitized["fallback"]["from_provider"] == "cornerstones_crypto"
    assert sanitized["fallback"]["to_provider"] == "cornerstones_crypto"
    assert sanitized["option_contract"]["fallback"] == "cornerstones_options_quote_missing"
    assert sanitized["option_contract"]["chain_fallback"] == "cornerstones_options_quotes_missing"
    assert sanitized["option_contract"]["partial_reason"] == "cornerstones_options_quotes_partial"
    assert sanitized["option_contract"]["empty_fallback"] == "cornerstones_options_empty"
    assert sorted(sanitized["providers"]) == ["cornerstones_equities", "cornerstones_market_data"]
    assert sanitized["orderflow"]["provider"] == "cornerstones_orderflow"
    assert sanitized["orderflow"]["provenance"] == "cornerstones_orderflow:stream"
    assert sanitized["chart"]["engine"] == "cornerstones_chart_renderer"
    for forbidden in ("mt5", "fmp", "rithmic", "adanos", "okx", "bybit", "oanda", "tradingview"):
        assert forbidden not in serialized.lower()
