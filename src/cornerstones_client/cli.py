from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

from .config import DEFAULT_API_BASE_URL, DEFAULT_PORTAL_BASE_URL, load_config, save_config


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _fail(error: str, message: str, *, status_code: int | None = None) -> None:
    payload: dict[str, Any] = {"error": error, "message": message}
    if status_code is not None:
        payload["status_code"] = status_code
    _print(payload)
    raise SystemExit(1)


def select_discovery_bearer(config: dict[str, Any]) -> str | None:
    return config.get("api_key") or config.get("trial_token")


def build_headers(config: dict[str, Any], *, allow_trial: bool = False, require_api_key: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {}
    bearer = config.get("api_key")
    if not bearer and allow_trial:
        bearer = config.get("trial_token")
    if require_api_key and not config.get("api_key"):
        _fail("not_logged_in", "Run auth login first.")
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
    config = _ensure_trial_token(load_config())
    with httpx.Client(timeout=20.0) as client:
        response = client.get(f"{_api_base_url(config)}{route}", headers=build_headers(config, allow_trial=True))
    if response.status_code >= 400:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        _fail(payload.get("error", "discovery_request_failed"), payload.get("message", response.text), status_code=response.status_code)
    _print(response.json())


def cmd_verify(_: argparse.Namespace) -> None:
    config = load_config()
    with httpx.Client(timeout=20.0) as client:
        response = client.get(f"{_api_base_url(config)}/v1/status", headers=build_headers(config, require_api_key=True))
    if response.status_code >= 400:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        _fail(payload.get("error", "verify_failed"), payload.get("message", response.text), status_code=response.status_code)
    _print(response.json())


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

    guide_parser = sub.add_parser("guide", help="Fetch product discovery surface using an API key or trial token")
    guide_parser.set_defaults(func=lambda args: _run_discovery_route("/v1/features"))

    changelog_parser = sub.add_parser("changelog", help="Fetch product changelog using an API key or trial token")
    changelog_parser.set_defaults(func=lambda args: _run_discovery_route("/v1/changelog"))

    verify_parser = sub.add_parser("verify", help="Verify a real authenticated API key against /v1/status")
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
