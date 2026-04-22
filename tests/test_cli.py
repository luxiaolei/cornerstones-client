from __future__ import annotations

import pytest

from cornerstones_client.cli import build_headers, main, select_discovery_bearer


def test_select_discovery_bearer_prefers_api_key_before_trial_token():
    config = {"api_key": "csk_live_secret", "trial_token": "ctrial_trial.secret", "trial_cookie": None}
    assert select_discovery_bearer(config) == "csk_live_secret"


def test_select_discovery_bearer_falls_back_to_trial_token():
    config = {"api_key": None, "trial_token": "ctrial_trial.secret", "trial_cookie": None}
    assert select_discovery_bearer(config) == "ctrial_trial.secret"


def test_build_headers_includes_cookie_and_selected_bearer():
    config = {
        "api_key": None,
        "trial_token": "ctrial_trial.secret",
        "trial_cookie": "cornerstones_trial_session=abc",
    }
    headers = build_headers(config, allow_trial=True)
    assert headers["Authorization"] == "Bearer ctrial_trial.secret"
    assert headers["Cookie"] == "cornerstones_trial_session=abc"


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
