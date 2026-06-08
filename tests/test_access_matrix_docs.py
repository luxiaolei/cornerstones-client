from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_docs_capture_current_access_matrix():
    combined = "\n".join([
        (ROOT / "README.md").read_text(),
        (ROOT / "docs" / "CLI_REFERENCE.md").read_text(),
        (ROOT / "docs" / "ACCESS_MATRIX.md").read_text(),
    ])

    for required in [
        "No-key public access includes selected basic market reads",
        "No-key/trial access is not discovery-only",
        "`/v1/changelog` is admin-only",
        "500 requests/month",
        "10 requests/minute",
        "Charts require **Pro+**",
        "Orderflow requires **Max**",
        "All `orderflow ...` commands are Max-only",
        "The key is a Cornerstones API key",
        "Current documented release: `0.1.21`",
        "stocks imbalance-window",
        "auction imbalance rolling window",
        "fx options-proxy",
        "fx positioning",
        "fx levels",
        "fx opening-range",
        "fx price-action",
        "fx volume-profile",
        "macro event-window",
        "support-only ETF options proxy evidence",
        "provider-availability contract",
        "stocks facts",
        "stocks transcripts",
        "stocks analyst-estimates",
        "stocks ratings",
        "stocks price-targets",
        "stocks ratios",
        "stocks key-metrics",
        "stocks extended-hours",
        "stocks research-context",
        "stock research inputs such as transcripts, analyst estimates, ratings, price targets, ratios, and key metrics",
        "filings --provider sec",
        "CORNERSTONES_SEC_USER_AGENT",
    ]:
        assert required in combined

    assert "provider credential" in combined

    research_copy = "\n".join(
        line for line in combined.splitlines() if "research" in line.lower() or "transcript" in line.lower()
    )
    assert "FMP" not in research_copy
