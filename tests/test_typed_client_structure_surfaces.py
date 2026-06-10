from __future__ import annotations

import json

import httpx

from cornerstones_client import (
    CornerstonesClient,
    FXBarsResponse,
    FXLevelsResponse,
    FXOpeningRangeResponse,
    FXPriceActionResponse,
    FXVolumeProfilePackResponse,
    FXVolumeProfileResponse,
    MacroEventWindowResponse,
)


class Recorder:
    def __init__(self, payloads: dict[str, dict]):
        self.payloads = payloads
        self.requests: list[httpx.Request] = []
        self.client = httpx.Client(transport=httpx.MockTransport(self._handle))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        payload = self.payloads[request.url.path]
        return httpx.Response(200, json=payload, request=request)


def _client(payloads: dict[str, dict]) -> tuple[CornerstonesClient, Recorder]:
    recorder = Recorder(payloads)
    test_key = "ck_test"
    return (
        CornerstonesClient(api_base_url="http://api.test", api_key=test_key, http_client=recorder.client),
        recorder,
    )


def test_typed_fx_methods_hit_structure_surface_routes_and_params():
    client, recorder = _client(
        {
            "/v1/fx/bars": {"symbol": "XAUUSD", "timeframe": "M15", "bars_count": 128, "count": 128, "bars": [], "as_of": "2026-05-26T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "mt5"},
            "/v1/fx/levels": {"symbol": "XAUUSD", "timeframe": "5m", "bars_count": 600, "current_price": 2350.25, "as_of": "2026-05-26T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "mt5"},
            "/v1/fx/opening-range": {"symbol": "XAUUSD", "session": "london", "minutes": 30, "window_minutes": 30, "as_of": "2026-05-26T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "mt5"},
            "/v1/fx/price-action": {"symbol": "XAUUSD", "timeframe": "H1", "bars_count": 120, "trend_state": "range", "as_of": "2026-05-26T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "mt5"},
            "/v1/fx/volume-profile": {"symbol": "XAUUSD", "timeframe": "15m", "basis": "gc_futures_orderflow_proxy", "source_symbol": "GC", "proxy": True, "profile_quality": "derived_orderflow_only", "as_of": "2026-05-26T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "orderflow"},
            "/v1/fx/volume-profile/pack": {"symbol": "XAUUSD", "source_symbol": "GC", "layer_order": ["micro_15m", "context_1h", "current_session"], "primary_layer": "micro_15m", "trade_grade_layers": ["current_session"], "all_layers_trade_grade": False, "layers": [{"layer": "micro_15m", "symbol": "XAUUSD", "timeframe": "15m", "basis": "gc_futures_orderflow_proxy", "source_symbol": "GC", "proxy": True}], "as_of": "2026-06-10T10:00:00Z", "freshness_status": "fresh", "degraded": False, "fallback": None, "provenance": "orderflow"},
        }
    )

    assert isinstance(client.fx.bars("XAUUSD", "M15", 128), FXBarsResponse)
    assert isinstance(client.fx.levels("XAUUSD"), FXLevelsResponse)
    assert isinstance(client.fx.opening_range("XAUUSD", "london", 30), FXOpeningRangeResponse)
    assert isinstance(client.fx.price_action("XAUUSD", "H1", 120), FXPriceActionResponse)
    volume_profile = client.fx.volume_profile("XAUUSD", "15m", basis="gc_futures")
    assert isinstance(volume_profile, FXVolumeProfileResponse)
    assert volume_profile.proxy is True
    assert volume_profile.source_symbol == "GC"
    assert volume_profile.basis == "gc_futures_orderflow_proxy"
    assert volume_profile.profile_quality == "derived_orderflow_only"
    assert volume_profile.to_dict()["source_symbol"] == "GC"
    profile_pack = client.fx.volume_profile_pack("XAUUSD", basis="gc_futures")
    assert isinstance(profile_pack, FXVolumeProfilePackResponse)
    assert profile_pack.layer_order == ["micro_15m", "context_1h", "current_session"]
    assert profile_pack.primary_layer == "micro_15m"
    assert profile_pack.trade_grade_layers == ["current_session"]
    assert profile_pack.all_layers_trade_grade is False
    assert profile_pack.layers[0]["layer"] == "micro_15m"

    assert [(req.url.path, dict(req.url.params)) for req in recorder.requests] == [
        ("/v1/fx/bars", {"symbol": "XAUUSD", "timeframe": "M15", "bars": "128"}),
        ("/v1/fx/levels", {"symbol": "XAUUSD"}),
        ("/v1/fx/opening-range", {"symbol": "XAUUSD", "session": "london", "minutes": "30"}),
        ("/v1/fx/price-action", {"symbol": "XAUUSD", "timeframe": "H1", "bars": "120"}),
        ("/v1/fx/volume-profile", {"symbol": "XAUUSD", "timeframe": "15m", "basis": "gc_futures"}),
        ("/v1/fx/volume-profile/pack", {"symbol": "XAUUSD", "basis": "gc_futures"}),
    ]
    assert all(req.headers["authorization"] == "Bearer ck_test" for req in recorder.requests)


def test_typed_models_preserve_common_contract_fields_and_raw_payload():
    payload = {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "bars_count": 120,
        "as_of": "2026-05-26T10:00:00Z",
        "freshness_status": "aging",
        "degraded": True,
        "fallback": {"reason": "source_empty", "source": "mt5"},
        "provenance": "runtime",
        "profile_quality": "derived_orderflow_only",
        "custom_future_field": {"kept": True},
    }

    model = FXPriceActionResponse.from_payload(payload)

    assert model.as_of == "2026-05-26T10:00:00Z"
    assert model.freshness_status == "aging"
    assert model.degraded is True
    assert model.fallback == {"reason": "source_empty", "source": "mt5"}
    assert model.provenance == "runtime"
    assert model.to_dict()["custom_future_field"] == {"kept": True}
    assert model["profile_quality"] == "derived_orderflow_only"


def test_public_docs_describe_typed_structure_client_and_safety_boundaries():
    from pathlib import Path

    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()

    for required in [
        "CornerstonesClient",
        "client.fx.levels(\"XAUUSD\")",
        "client.fx.opening_range(\"XAUUSD\", session=\"london\", minutes=30)",
        "client.fx.price_action(\"XAUUSD\", timeframe=\"H1\", bars=120)",
        "client.fx.volume_profile(\"XAUUSD\", timeframe=\"15m\", basis=\"gc_futures\")",
        "client.fx.volume_profile_pack(\"XAUUSD\", basis=\"gc_futures\")",
        "client.macro.event_window(\"XAUUSD\", currency=\"USD\", importance=\"high\")",
        "no trading recommendation, account, risk, or execution permissions",
        "XAU volume profile is a GC futures proxy, not spot centralized volume",
    ]:
        assert required in readme


def test_typed_macro_event_window_hits_route_and_preserves_safety_fields():
    client, recorder = _client(
        {
            "/v1/macro/event-window": {
                "symbol": "XAUUSD",
                "currency": "USD",
                "as_of": "2026-05-26T10:00:00Z",
                "freshness_status": "fresh",
                "event_window_state": "event_imminent",
                "blackout_suggestion": {"reduce_new_entries": True},
                "events": [],
                "degraded": False,
                "fallback": None,
                "provenance": "macro_service",
            }
        }
    )

    model = client.macro.event_window("XAUUSD", currency="USD", importance="high")

    assert isinstance(model, MacroEventWindowResponse)
    assert model.currency == "USD"
    assert model.event_window_state == "event_imminent"
    assert model.blackout_suggestion == {"reduce_new_entries": True}
    req = recorder.requests[-1]
    assert req.url.path == "/v1/macro/event-window"
    assert dict(req.url.params) == {"symbol": "XAUUSD", "currency": "USD", "importance": "high"}
    assert "recommendation" not in json.dumps(model.to_dict()).lower()
    assert "execution" not in json.dumps(model.to_dict()).lower()
