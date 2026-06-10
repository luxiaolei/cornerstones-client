from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Self

import httpx

from .config import DEFAULT_API_BASE_URL, load_config


def _compact_params(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True)
class ContractResponse:
    """Shape-preserving typed wrapper for Cornerstones API responses."""

    raw: dict[str, Any] = field(default_factory=dict)
    as_of: str | None = None
    freshness_status: str | None = None
    degraded: bool | None = None
    fallback: Any = None
    provenance: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        known = {f.name for f in fields(cls)}
        values = {name: payload.get(name) for name in known if name != "raw" and name in payload}
        return cls(raw=dict(payload), **values)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]


@dataclass(frozen=True)
class FXBarsResponse(ContractResponse):
    symbol: str | None = None
    timeframe: str | None = None
    count: int | None = None
    bars_count: int | None = None
    bars: list[dict[str, Any]] = field(default_factory=list)
    data_quality: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FXLevelsResponse(ContractResponse):
    symbol: str | None = None
    current_price: float | None = None
    timeframe: str | None = None
    bars_count: int | None = None
    prior_day: dict[str, Any] | None = None
    current_day: dict[str, Any] = field(default_factory=dict)
    sessions: dict[str, Any] = field(default_factory=dict)
    distance_to_levels: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FXOpeningRangeResponse(ContractResponse):
    symbol: str | None = None
    session: str | None = None
    window_minutes: int | None = None
    minutes: int | None = None
    session_open: str | None = None
    range_high: float | None = None
    range_low: float | None = None
    range_mid: float | None = None
    range_size: float | None = None
    current_position: str | None = None
    breakout_state: str | None = None
    minutes_since_session_open: int | None = None


@dataclass(frozen=True)
class FXPriceActionResponse(ContractResponse):
    symbol: str | None = None
    timeframe: str | None = None
    bars_count: int | None = None
    current_price: float | None = None
    lookback_high: float | None = None
    lookback_low: float | None = None
    range_position: float | None = None
    last_bar_direction: str | None = None
    body_to_range_ratio: float | None = None
    higher_highs_count: int | None = None
    higher_lows_count: int | None = None
    lower_highs_count: int | None = None
    lower_lows_count: int | None = None
    trend_state: str | None = None
    breakout_state: str | None = None


@dataclass(frozen=True)
class FXVolumeProfileResponse(ContractResponse):
    symbol: str | None = None
    timeframe: str | None = None
    basis: str | None = None
    source_symbol: str | None = None
    proxy: bool | None = None
    spot_volume_truth: bool | None = None
    base_bucket: str | None = None
    base_bucket_count: int | None = None
    profile_quality: str | None = None
    poc: float | None = None
    vah: float | None = None
    val: float | None = None
    profile_buckets: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class FXVolumeProfilePackResponse(ContractResponse):
    symbol: str | None = None
    source_symbol: str | None = None
    layer_order: list[str] = field(default_factory=list)
    primary_layer: str | None = None
    trade_grade_layers: list[str] = field(default_factory=list)
    all_layers_trade_grade: bool | None = None
    layers: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MacroEventWindowResponse(ContractResponse):
    symbol: str | None = None
    currency: str | None = None
    lookback_minutes: int | None = None
    lookahead_minutes: int | None = None
    active_window: bool | None = None
    event_window_state: str | None = None
    next_event_at: str | None = None
    next_event: dict[str, Any] | None = None
    blackout_suggestion: dict[str, bool] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    filters: dict[str, str] = field(default_factory=dict)


class CornerstonesAPIError(RuntimeError):
    """Raised when Core API returns an error response."""

    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self.payload = payload or {}
        self.text = text
        message = self.payload.get("message") or self.payload.get("error") or text or f"HTTP {status_code}"
        super().__init__(str(message))


class CornerstonesClient:
    """Typed sync client for customer-safe Cornerstones read surfaces."""

    def __init__(
        self,
        *,
        api_base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        config = load_config()
        self.api_base_url = (api_base_url or config.get("api_base_url") or DEFAULT_API_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else config.get("api_key")
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_client = http_client is None
        self.fx = FXNamespace(self)
        self.macro = MacroNamespace(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _get(self, route: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = self._client.get(f"{self.api_base_url}{route}", headers=headers, params=params)
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = None
            raise CornerstonesAPIError(response.status_code, payload if isinstance(payload, dict) else None, response.text)
        payload = response.json()
        if not isinstance(payload, dict):
            return {"data": payload}
        return payload


class FXNamespace:
    def __init__(self, client: CornerstonesClient) -> None:
        self._client = client

    def bars(self, symbol: str, timeframe: str = "1h", bars: int = 10) -> FXBarsResponse:
        payload = self._client._get(
            "/v1/fx/bars",
            params=_compact_params({"symbol": symbol, "timeframe": timeframe, "bars": bars}),
        )
        return FXBarsResponse.from_payload(payload)

    def levels(self, symbol: str, timeframe: str | None = None, bars: int | None = None) -> FXLevelsResponse:
        payload = self._client._get(
            "/v1/fx/levels",
            params=_compact_params({"symbol": symbol, "timeframe": timeframe, "bars": bars}),
        )
        return FXLevelsResponse.from_payload(payload)

    def opening_range(
        self,
        symbol: str,
        session: str = "london",
        minutes: int = 30,
        timeframe: str | None = None,
        bars: int | None = None,
    ) -> FXOpeningRangeResponse:
        payload = self._client._get(
            "/v1/fx/opening-range",
            params=_compact_params(
                {"symbol": symbol, "session": session, "minutes": minutes, "timeframe": timeframe, "bars": bars}
            ),
        )
        return FXOpeningRangeResponse.from_payload(payload)

    def price_action(self, symbol: str, timeframe: str = "H1", bars: int = 120) -> FXPriceActionResponse:
        payload = self._client._get(
            "/v1/fx/price-action",
            params=_compact_params({"symbol": symbol, "timeframe": timeframe, "bars": bars}),
        )
        return FXPriceActionResponse.from_payload(payload)

    def volume_profile(
        self,
        symbol: str,
        timeframe: str = "15m",
        *,
        basis: str = "gc_futures",
    ) -> FXVolumeProfileResponse:
        payload = self._client._get(
            "/v1/fx/volume-profile",
            params=_compact_params({"symbol": symbol, "timeframe": timeframe, "basis": basis}),
        )
        return FXVolumeProfileResponse.from_payload(payload)

    def volume_profile_pack(
        self,
        symbol: str,
        *,
        basis: str = "gc_futures",
    ) -> FXVolumeProfilePackResponse:
        payload = self._client._get(
            "/v1/fx/volume-profile/pack",
            params=_compact_params({"symbol": symbol, "basis": basis}),
        )
        return FXVolumeProfilePackResponse.from_payload(payload)


class MacroNamespace:
    def __init__(self, client: CornerstonesClient) -> None:
        self._client = client

    def event_window(
        self,
        symbol: str,
        currency: str | None = None,
        importance: str | None = None,
        lookback_minutes: int | None = None,
        lookahead_minutes: int | None = None,
    ) -> MacroEventWindowResponse:
        payload = self._client._get(
            "/v1/macro/event-window",
            params=_compact_params(
                {
                    "symbol": symbol,
                    "currency": currency,
                    "importance": importance,
                    "lookback_minutes": lookback_minutes,
                    "lookahead_minutes": lookahead_minutes,
                }
            ),
        )
        return MacroEventWindowResponse.from_payload(payload)
