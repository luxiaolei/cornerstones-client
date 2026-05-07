from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import RuntimeConfig
from .routes import RouteSpec


class FastPathFallback(Exception):
    """Signal that legacy core CLI should handle this argv."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


urlopen = build_opener(_NoRedirectHandler).open


class MissingAuth(Exception):
    """Auth-required route has no bearer token."""


@dataclass(frozen=True)
class FastPathHTTPError(Exception):
    status_code: int
    url: str
    body: str

    def payload(self) -> dict[str, Any]:
        return {
            "error": "http_error",
            "status_code": self.status_code,
            "url": _redact_url(self.url),
            "body": _redact_body(self.body),
        }


@dataclass(frozen=True)
class FastPathRequestFailed(Exception):
    url: str
    message: str

    def payload(self) -> dict[str, Any]:
        return {"error": "request_failed", "url": _redact_url(self.url), "message": _redact_body(self.message)}


def _url_with_params(base: str, params: dict[str, Any]) -> str:
    if not params:
        return base
    return f"{base}?{urlencode(params, doseq=True)}"


def _redact_body(text: str, *, max_chars: int = 2000) -> str:
    redacted = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", text)
    redacted = re.sub(
        r"(?i)(api[_-]?key|token|password|secret|authorization)([\"'\s:=]+)([^\s,}\]\"']+)",
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]",
        redacted,
    )
    if len(redacted) > max_chars:
        return f"{redacted[:max_chars]}... [truncated]"
    return redacted


def _redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = host
        if parts.port is not None:
            netloc = f"{netloc}:{parts.port}"
        query = urlencode(
            [
                (key, "[REDACTED]" if re.search(r"(?i)(api[_-]?key|token|password|secret|authorization)", key) else value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
            ],
            doseq=True,
        )
        return urlunsplit((parts.scheme, netloc, parts.path, query, ""))
    except Exception:
        return _redact_body(url)


def _read_error_body(exc: HTTPError) -> str:
    try:
        return _redact_body(exc.read().decode("utf-8", errors="replace"))
    except Exception:
        return _redact_body(str(exc))


def request_json(spec: RouteSpec, config: RuntimeConfig) -> dict[str, Any]:
    url = _url_with_params(f"{config.base_url}{spec.path}", spec.params)
    headers: dict[str, str] = {}
    data: bytes | None = None
    auth_header: str | None = None
    if config.api_key:
        auth_header = f"Bearer {config.api_key}"
    elif spec.auth_required:
        raise MissingAuth()
    if auth_header:
        headers["Authorization"] = auth_header
    if spec.json_body is not None:
        data = json.dumps(spec.json_body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=spec.method)
    try:
        with urlopen(request, timeout=spec.timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status_code = getattr(response, "status", response.getcode())
    except HTTPError as exc:
        if exc.code in {404, 405, 501} or (exc.code in {401, 403} and not spec.auth_required and not config.api_key):
            raise FastPathFallback(f"unsupported by running server: {exc.code}") from exc
        raise FastPathHTTPError(exc.code, url, _read_error_body(exc)) from exc
    except URLError as exc:
        raise FastPathFallback(str(exc)) from exc

    if status_code in {404, 405, 501} or (status_code in {401, 403} and not spec.auth_required and not config.api_key):
        raise FastPathFallback(f"unsupported by running server: {status_code}")
    if status_code >= 400:
        raise FastPathHTTPError(status_code, url, _redact_body(body))

    try:
        payload = json.loads(body)
    except Exception as exc:
        raise FastPathRequestFailed(url, f"invalid JSON response: {exc}") from exc
    if isinstance(payload, dict):
        return payload
    return {"data": payload}
