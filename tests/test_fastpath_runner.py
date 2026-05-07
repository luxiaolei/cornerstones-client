from __future__ import annotations

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
        (["health", "status"], "GET", "/health", {}, False),
        (["context", "fx", "--symbol", "EURUSD", "--timeframe", "M15", "--count", "3"], "GET", "/v1/context/fx", {"symbol": "EURUSD", "timeframe": "M15", "count": 3}, True),
        (["fx", "quote", "--symbol", "EURUSD"], "GET", "/v1/fx/quote", {"symbol": "EURUSD"}, True),
        (["fx", "bars", "--symbol", "EURUSD", "--timeframe", "M15"], "GET", "/v1/fx/bars", {"symbol": "EURUSD", "timeframe": "M15"}, True),
        (["fx", "indicators", "--symbol", "EURUSD", "--timeframe", "M15", "--bars", "200"], "GET", "/v1/fx/indicators", {"symbol": "EURUSD", "timeframe": "M15", "bars": 200}, True),
        (["fx", "session", "--symbol", "EURUSD", "--timeframe", "M15", "--bars", "200"], "GET", "/v1/fx/session", {"symbol": "EURUSD", "timeframe": "M15", "bars": 200}, True),
        (["cross-asset", "context"], "GET", "/v1/cross-asset/context", {}, True),
        (["stocks", "quote", "--symbol", "GLD"], "GET", "/v1/stocks/quote", {"symbol": "GLD"}, True),
        (["stocks", "context", "--symbol", "GLD", "--bars-count", "3"], "GET", "/v1/stocks/context", {"symbol": "GLD", "bars_count": 3}, True),
        (["context", "gold"], "GET", "/v1/context/gold", {}, True),
        (["gold", "context"], "GET", "/v1/gold/context", {}, True),
    ]

    for argv, method, path, params, auth_required in cases:
        spec = match_route(argv)
        assert spec is not None, argv
        assert spec.method == method
        assert spec.path == path
        assert spec.params == params
        assert spec.auth_required is auth_required


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


def test_fastpath_config_env_base_is_explicit_override(monkeypatch, tmp_path):
    from cornerstones_client.fastpath.config import load_runtime_config

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CORNERSTONES_BASE_URL", "http://env-api.test")
    monkeypatch.setenv("CORNERSTONES_API_KEY", "env")

    config = load_runtime_config()

    assert config.base_url == "http://env-api.test"
    assert config.api_key == "env"
    assert config.source == "env"


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
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        calls.append((request.get_method(), request.full_url, request.get_header("Authorization")))
        return FakeResponse()

    monkeypatch.setattr(fast_http, "urlopen", fake_urlopen)

    assert run(["fx", "quote", "--symbol", "EURUSD"]) == 0
    assert calls == [("GET", "http://api.test/v1/fx/quote?symbol=EURUSD", "Bearer test")]
    assert json.loads(capsys.readouterr().out) == {"ok": True}


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
