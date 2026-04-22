from pathlib import Path

from cornerstones_client.config import load_config, save_config


def test_load_config_defaults_include_portal_and_api_urls(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_PORTAL_BASE_URL", "http://127.0.0.1:3001")
    monkeypatch.setenv("CORNERSTONES_API_BASE_URL", "http://127.0.0.1:8100")

    config = load_config()

    assert config["portal_base_url"] == "http://127.0.0.1:3001"
    assert config["api_base_url"] == "http://127.0.0.1:8100"
    assert config["api_key"] is None
    assert config["trial_cookie"] is None
    assert config["trial_token"] is None


def test_save_config_roundtrip_preserves_trial_token(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    payload = {
        "portal_base_url": "http://portal.example",
        "api_base_url": "http://api.example",
        "api_key": "csk_live_secret",
        "trial_cookie": "cornerstones_trial_session=abc",
        "trial_token": "ctrial_abc.def",
    }
    path = save_config(payload)

    assert Path(path).exists()
    reloaded = load_config()
    assert reloaded == payload
