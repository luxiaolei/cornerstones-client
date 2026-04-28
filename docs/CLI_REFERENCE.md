# Cornerstones Client CLI Reference

Customer-facing command reference for `cornerstones-client`.

This file mirrors the README command surface in a compact format for operators and AI agents. It documents customer-safe reads plus customer-owned alert/event subscription flows, not admin/operator internals.

## Install

```bash
python -m pip install -U cornerstones-client==0.1.8
```

## Configuration

Default production endpoints:

- portal: `https://www.usecornerstones.com`
- API: `https://api.usecornerstones.com`

Local config path:

```text
~/.config/cornerstones-client/config.json
```

Commands:

```bash
cornerstones-client auth status
cornerstones-client auth login --api-key <issued-api-key>
cornerstones-client auth logout
cornerstones-client auth set-base-url --base-url <portal-url>
cornerstones-client auth set-api-base-url --api-base-url <api-url>
```

## Discovery

```bash
cornerstones-client guide
cornerstones-client changelog
```

`guide` returns server-owned product discovery and contract rules. `changelog` returns customer-safe release notes.

## Verification

```bash
cornerstones-client verify
```

Calls authenticated `/v1/status`.

## FX / currency pairs

Use `fx` for direct pair data.

```bash
cornerstones-client fx quote --symbol EURUSD
cornerstones-client fx bars --symbol EURUSD --timeframe 1h --count 50
cornerstones-client fx indicators --symbol USDJPY --timeframe H1 --bars 200
cornerstones-client fx session --symbol GBPUSD --timeframe H1 --bars 200
```

Common symbols tested during documentation refresh:

- `EURUSD`
- `GBPUSD`
- `USDJPY`
- `AUDUSD`
- `USDCAD`
- `USDCHF`
- `NZDUSD`
- `XAUUSD`

## Context packages

Use `context` for packaged multi-provider context.

```bash
cornerstones-client context fx --symbol XAUUSD --timeframe 1h --count 3
cornerstones-client context gold --symbol XAUUSD --timeframe 1h --count 3
cornerstones-client context stocks --symbol AAPL --timeframe 1d --count 3
```

Interpretation:

- `context fx` can include quote, bars, sentiment, narrative, event, and optional enrichment blocks.
- Non-gold FX pair quote/bars can be healthy even if optional sentiment/narrative sources return `source_empty`.
- `context stocks` treats quote/profile/bars as core components. Supplementary depth/imbalance may be unavailable without degrading the root context.

## Order-flow

Read-only order-flow surfaces are exposed for XAUUSD/GC-style microstructure consumers. Admin collection/job controls remain operator-only.

```bash
cornerstones-client orderflow summary --symbol XAUUSD
cornerstones-client orderflow context --symbol XAUUSD
cornerstones-client orderflow raw --symbol XAUUSD
cornerstones-client orderflow historical --symbol XAUUSD
cornerstones-client orderflow liquidity-metrics --symbol XAUUSD
```

## Charts

Charts render server-side artifacts and return JSON metadata with artifact URLs.

```bash
cornerstones-client chart fx --symbol XAUUSD --timeframe H1 --bars 120
cornerstones-client chart stocks --symbol AAPL --timeframe 1d --bars 120
```

Common flags: `--indicator`, `--template`, `--layout`, `--layer`, `--include`, `--chart-type`, `--width`, `--height`.

## Additional non-admin read groups

Additional non-admin read groups in `0.1.7`:

```bash
cornerstones-client crypto quote --symbol BTCUSDT
cornerstones-client crypto bars --symbol BTCUSDT --timeframe 1h --count 100
cornerstones-client stocks quote --symbol AAPL
cornerstones-client stocks screener --limit 25
cornerstones-client stocks universe --preset us-stocks-liquid --limit 25
cornerstones-client options chain --symbol AAPL --max-expirations 1
cornerstones-client macro summary
cornerstones-client macro series --name CPIAUCSL
cornerstones-client geopolitics status
cornerstones-client geopolitics osint-feed --limit 20
cornerstones-client polymarket overview
cornerstones-client events recent --limit 20
cornerstones-client cross-asset
```

## Evidence

```bash
cornerstones-client evidence feed --asset XAUUSD --limit 5
cornerstones-client evidence feed --asset XAUUSD --type alert --priority critical --limit 10
```

Evidence feed is live-backed from the alerts store and returns raw evidence items. It does not fabricate sentiment aggregation.

## Alerts

```bash
cornerstones-client alerts metrics
cornerstones-client alerts recent --limit 5
cornerstones-client alerts dead-letter --limit 5
cornerstones-client alerts list
cornerstones-client alerts show --subscription-id sub_xxx
cornerstones-client alerts subscribe --asset XAUUSD --lane macro_event_window --webhook-url https://client.example.com/alerts --signing-secret-env CLIENT_SIGNING_SECRET --require-signing
cornerstones-client alerts delete --subscription-id sub_xxx
```

`alerts subscribe` and `alerts delete` are customer-owned subscription management. Admin/operator alert dispatch, replay, resolve, and test remain excluded. Prefer `--signing-secret-env` over `--signing-secret` so secrets do not appear in shell history.

## Events

```bash
cornerstones-client events recent --limit 20
cornerstones-client events history --symbol XAUUSD --limit 50
cornerstones-client events receipts --limit 50
cornerstones-client events subscribe --symbol XAUUSD --family scheduled_macro --min-severity medium --webhook-url https://client.example.com/events --signing-secret-env CLIENT_SIGNING_SECRET --require-signing
```

`events subscribe` creates a customer-owned event subscription. Event receipt submission/export remain excluded from the public client.

## Trial onboarding

```bash
cornerstones-client trial start
cornerstones-client trial status
cornerstones-client trial token
```

Trial flows are limited discovery/onboarding helpers. Full market data reads require an issued API key.

## Core API alignment matrix

| Core path | Client command |
|---|---|
| `/v1/status` | `verify` |
| `/v1/features` | `guide` |
| `/v1/changelog` | `changelog` |
| `/v1/fx/quote` | `fx quote` |
| `/v1/fx/bars` | `fx bars` |
| `/v1/fx/indicators` | `fx indicators` |
| `/v1/fx/session` | `fx session` |
| `/v1/context/fx` | `context fx` |
| `/v1/gold/context` | `context gold` |
| `/v1/stocks/context` | `context stocks` |
| `/v1/orderflow/summary` | `orderflow summary` |
| `/v1/orderflow/context` | `orderflow context` |
| `/v1/orderflow/raw` | `orderflow raw` |
| `/v1/orderflow/historical` | `orderflow historical` |
| `/v1/orderflow/liquidity-metrics` | `orderflow liquidity-metrics` |
| `/v1/fx/chart` | `chart fx` |
| `/v1/stocks/chart` | `chart stocks` |
| `/v1/evidence/feed` | `evidence feed` |
| `/v1/alerts/metrics` | `alerts metrics` |
| `/v1/alerts/recent` | `alerts recent` |
| `/v1/alerts/dead-letter` | `alerts dead-letter` |
| `/v1/alerts/subscribe` | `alerts subscribe` |
| `/v1/alerts/{subscription_id}` | `alerts show` / `alerts delete` |
| `/v1/events/subscribe` | `events subscribe` |
| `/v1/events/recent` | `events recent` |
| `/v1/events/history` | `events history` |
| `/v1/events/receipts` | `events receipts` |

Not exposed in the client: admin/operator endpoints, destructive mutations, order-flow collection jobs, alert dispatch/replay/resolve/test, event receipt submission/export, internal maintenance, and direct artifact-download helpers beyond returned chart URLs. Customer-owned alert/event subscribe flows are exposed.

## Output contract

Always inspect these fields when present:

- `provenance`
- `degraded`
- `fallback`
- `not_implemented`
- `data_quality`

HTTP success and data quality are separate. A response can be HTTP 200 with `degraded: true`; that means the request worked but the data source/path is incomplete or reduced quality.

## Safe support output

When sharing examples publicly, redact:

- API keys
- key IDs
- Authorization headers
- cookies
- customer/user subjects
- webhook targets
- delivery destinations
