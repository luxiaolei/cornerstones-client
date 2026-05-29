from __future__ import annotations

import re
from typing import Any


_EXACT_VALUE_REPLACEMENTS = {
    "mt5": "cornerstones_market_data",
    "fmp": "cornerstones_equities",
    "rithmic": "cornerstones_orderflow",
    "adanos": "cornerstones_context",
    "okx": "cornerstones_crypto",
    "bybit": "cornerstones_crypto",
    "ib": "cornerstones_options",
    "ibkr": "cornerstones_options",
    "fred": "cornerstones_macro",
    "oanda": "FX",
    "tradingview": "cornerstones_chart_renderer",
    "tradingview_widget_local": "cornerstones_chart_renderer",
    "cornerstones+rithmic": "cornerstones_orderflow",
    "cornerstones+rithmic:stream": "cornerstones_orderflow:stream",
    "cornerstones+rithmic:probe": "cornerstones_orderflow:probe",
    "cornerstones+ib:depth": "cornerstones_options:depth",
    "cornerstones+ib:top_of_book": "cornerstones_options:top_of_book",
    "ib_depth": "cornerstones_options_depth",
    "ib_options_primary": "cornerstones_options_primary",
    "ib_gateway_unavailable": "cornerstones_options_gateway_unavailable",
    "ib_not_connected": "cornerstones_options_not_connected",
    "ib_underlying_unqualified": "cornerstones_options_underlying_unqualified",
    "ib_underlying_quote_missing": "cornerstones_options_underlying_quote_missing",
    "ib_no_options_chain": "cornerstones_options_no_options_chain",
    "ib_options_timeout": "cornerstones_options_timeout",
    "ib_options_empty": "cornerstones_options_empty",
    "ib_options_error": "cornerstones_options_error",
    "ib_options_quote_missing": "cornerstones_options_quote_missing",
    "ib_options_quotes_missing": "cornerstones_options_quotes_missing",
    "ib_options_quotes_partial": "cornerstones_options_quotes_partial",
    "ib_market_data_competing_live_session": "cornerstones_options_competing_live_session",
    "fmp_options_experimental": "cornerstones_options_public_fallback",
    "mt5+fmp+fmp+fmp+adanos": "cornerstones_gold_context",
}

def _provider_token(value: str) -> re.Pattern[str]:
    return re.compile(rf"(?i)(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])")


_TOKEN_REPLACEMENTS = (
    (_provider_token("MT5"), "cornerstones_market_data"),
    (_provider_token("FMP"), "cornerstones_equities"),
    (_provider_token("Rithmic"), "cornerstones_orderflow"),
    (_provider_token("Adanos"), "cornerstones_context"),
    (_provider_token("OKX"), "cornerstones_crypto"),
    (_provider_token("Bybit"), "cornerstones_crypto"),
    (_provider_token("IBKR"), "cornerstones_options"),
    (_provider_token("IB"), "cornerstones_options"),
    (_provider_token("FRED"), "cornerstones_macro"),
    (_provider_token("OANDA"), "FX"),
    (_provider_token("TradingView"), "cornerstones_chart_renderer"),
)


def sanitize_public_payload(value: Any) -> Any:
    """Normalize public payloads so upstream vendor labels do not leak."""
    if isinstance(value, dict):
        return {
            sanitize_public_string(key) if isinstance(key, str) else key: sanitize_public_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_public_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_public_payload(item) for item in value)
    if isinstance(value, str):
        return sanitize_public_string(value)
    return value


def sanitize_public_string(value: str) -> str:
    exact = _EXACT_VALUE_REPLACEMENTS.get(value.strip().lower())
    if exact is not None:
        return exact

    sanitized = value
    for pattern, replacement in _TOKEN_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
