# Cornerstones Access Matrix

This is the customer-facing product contract for the public `cornerstones-client` package. Runtime enforcement, website pricing, dashboard quickstarts, and docs should stay aligned with this matrix.

## Plans

- No-key public access includes selected basic market reads: FX quote and bars, crypto quote, bars, and ticker, stock symbol normalization, exchanges, quote, profile, screener, and universe, plus macro summary and calendar. No-key/trial access is not discovery-only, but signed browser/trial tokens are not API keys.
- Free API key: 500 requests/month, 10 requests/minute. Basic authenticated market truth is allowed; charts, orderflow, Layer 5 context, options analysis, macro exact series, and event export are not Free surfaces.
- Pro API key: 10,000 requests/month, 60 requests/minute. Adds chart artifacts, Layer 5 agent context, options chain/wall/analysis, macro exact series, and event export.
- Max API key: custom/unlimited request ceiling. Adds orderflow raw/summary/context/historical reads and liquidity metrics.

## Surface gates

- Discovery: `guide` and `/v1/features` expose public/optional-auth product discovery. `/v1/changelog` is admin-only; public release notes live in website/package docs.
- Verification: `verify` / `/v1/status` requires a real issued API key.
- No-key basic market truth: FX quote and bars; crypto quote, bars, and ticker; stock symbol normalization, exchanges, quote, profile, screener, and universe; macro summary and calendar.
- Issued-key basic market truth: FX indicators/session, FX `fx options-proxy` support-only ETF options proxy evidence, FX `fx positioning` provider-availability contract, authenticated crypto market depth/trades/session/indicators, stock context-adjacent reads, stock `filings --provider sec` and `stocks facts` official SEC reads, and stock research inputs such as transcripts, analyst estimates, ratings, price targets, ratios, and key metrics may fit Free quota when not explicitly premium-gated.
- Stock research MVP A: `stocks transcripts`, `stocks analyst-estimates`, `stocks ratings`, `stocks price-targets`, `stocks ratios`, `stocks key-metrics`, and `stocks research-context` expose neutral read-only evidence surfaces.
- Charts: `chart fx` and `chart stocks` require Pro or Max.
- Agent context: `context fx`, `context gold`, `cross-asset` require Pro or Max.
- Options: `options chain`, `options wall`, and `options analysis` require Pro or Max.
- Macro exact series: `macro series` requires Pro or Max.
- Events export: premium event export requires Pro or Max; customer-owned alert/event subscription management remains bounded and authenticated.
- Orderflow: `orderflow raw`, `orderflow summary`, `orderflow context`, `orderflow historical`, and `orderflow liquidity-metrics` require Max.

## Agent prompt

Give the agent the install block first:

```bash
python -m pip install cornerstones-client
cornerstones-client --help
```

After you issue an API key in the dashboard, give the agent the whole quickstart block:

```bash
cornerstones-client auth login --api-key <issued-api-key>
cornerstones-client verify
cornerstones-client guide
```

The key is a Cornerstones API key, not an upstream provider credential. The agent should store it with `auth login`, verify access, then inspect `guide` before choosing deeper commands.
