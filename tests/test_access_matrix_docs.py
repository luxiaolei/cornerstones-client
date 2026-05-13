from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_docs_capture_current_access_matrix():
    combined = "\n".join([
        (ROOT / "README.md").read_text(),
        (ROOT / "docs" / "CLI_REFERENCE.md").read_text(),
        (ROOT / "docs" / "ACCESS_MATRIX.md").read_text(),
    ])

    for required in [
        "discovery-only",
        "500 requests/month",
        "10 requests/minute",
        "Charts require **Pro+**",
        "Orderflow requires **Max**",
        "All `orderflow ...` commands are Max-only",
        "The key is a Cornerstones API key",
        "Current documented release: `0.1.16`",
        "fx options-proxy",
        "fx positioning",
        "support-only ETF options proxy evidence",
        "provider-availability contract",
    ]:
        assert required in combined

    assert "provider credential" in combined
