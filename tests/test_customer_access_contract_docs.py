from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "ACCESS_MATRIX.md",
    ROOT / "docs" / "CLI_REFERENCE.md",
]
BANNED_PROVIDER_STRINGS = [
    "fmp",
    "ib",
    "okx",
    "bybit",
    "mt5",
    "rithmic",
    "gamma",
    "adanos",
    "fred",
]
BANNED_PROVIDER_PATTERN = re.compile(
    rf"(?i)\b(?:{'|'.join(BANNED_PROVIDER_STRINGS)})\b"
)


def _combined_public_docs() -> str:
    return "\n".join(path.read_text() for path in PUBLIC_DOCS)


def test_public_docs_match_no_key_basic_market_contract():
    combined = _combined_public_docs()

    for required in [
        "No-key public access includes selected basic market reads",
        "No-key/trial access is not discovery-only",
        "FX quote and bars",
        "crypto quote, bars, and ticker",
        "stock symbol normalization, exchanges, quote, profile, screener, and universe",
        "macro summary and calendar",
        "verify` / `/v1/status` requires a real issued API key",
        "`/v1/changelog` is admin-only",
    ]:
        assert required in combined

    for stale in [
        "Trial/no-key access is discovery-only",
        "Trial / no-key: discovery-only",
        "Trial/no-key: discovery-only",
        "`/v1/changelog` work with a trial token or API key",
        "`guide` and `changelog` can use a signed discovery token",
        "market-data reads require a real issued API key",
    ]:
        assert stale not in combined

    assert not BANNED_PROVIDER_PATTERN.search(combined)
