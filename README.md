# Cornerstones Client

`cornerstones-client` is the customer-facing command-line client for the managed Cornerstones market-context API.

It gives traders, operators, and AI agents a safe local CLI for:

- storing a Cornerstones API key locally
- checking whether the key works
- discovering available managed product surfaces
- reading FX/currency-pair quotes, bars, indicators, and session state
- reading market context packages for FX, gold, and stocks
- reading XAUUSD/GC order-flow summaries, raw snapshots, history, and liquidity metrics
- rendering FX and stock chart artifacts
- reading live-backed evidence feed items
- checking alert metrics, recent alerts, and dead-letter status

The package is intentionally read-focused. It does **not** expose destructive admin, replay, subscription-management, or internal maintenance endpoints.

## Install

```bash
python -m pip install -U cornerstones-client
```

Pin the current documented release:

```bash
python -m pip install -U cornerstones-client==0.1.7
```

Requirements:

- Python `>=3.11`
- network access to the Cornerstones API
- an issued Cornerstones API key for authenticated data reads

## Default endpoints

By default the client points to hosted production endpoints:

| Purpose | Default |
|---|---|
| Portal | `https://www.usecornerstones.com` |
| API | `https://api.usecornerstones.com` |

Local/dev operators can override these:

```bash
cornerstones-client auth set-base-url --base-url http://127.0.0.1:3001
cornerstones-client auth set-api-base-url --api-base-url http://127.0.0.1:8100
```

You can also set environment defaults before first use:

```bash
export CORNERSTONES_PORTAL_BASE_URL=https://www.usecornerstones.com
export CORNERSTONES_API_BASE_URL=https://api.usecornerstones.com
```

## Quick start

```bash
# 1) Install
python -m pip install -U cornerstones-client

# 2) Save your issued API key locally
cornerstones-client auth login --api-key ck_your_issued_key_here

# 3) Verify the key
cornerstones-client verify

# 4) Read market data and context
cornerstones-client fx quote --symbol EURUSD
cornerstones-client fx indicators --symbol USDJPY --timeframe H1 --bars 200
cornerstones-client context fx --symbol XAUUSD --timeframe 1h --count 3
cornerstones-client orderflow summary --symbol XAUUSD
cornerstones-client chart fx --symbol XAUUSD --timeframe H1 --bars 120
cornerstones-client evidence feed --asset XAUUSD --limit 5
```

## Authentication and local config

The client stores local state in the user config directory:

```text
~/.config/cornerstones-client/config.json
```

Stored fields:

| Field | Meaning |
|---|---|
| `portal_base_url` | Product portal URL used for trial/onboarding calls |
| `api_base_url` | Cornerstones Core API URL |
| `api_key` | Issued API key, stored locally |
| `trial_cookie` | Browser-compatible trial session cookie, when used |
| `trial_token` | Short-lived discovery token, when used |

Check current local state:

```bash
cornerstones-client auth status
```

Example output from a fresh config:

```json
{
  "portal_base_url": "https://www.usecornerstones.com",
  "api_base_url": "https://api.usecornerstones.com",
  "logged_in": false,
  "has_trial_cookie": false,
  "has_trial_token": false
}
```

Save an issued key:

```bash
cornerstones-client auth login --api-key ck_your_issued_key_here
```

Example output:

```json
{
  "logged_in": true,
  "api_base_url": "https://api.usecornerstones.com"
}
```

Remove the saved key:

```bash
cornerstones-client auth logout
```

## Verify an API key

`verify` calls the authenticated `/v1/status` surface.

```bash
cornerstones-client verify
```

Real output shape, with sensitive identity fields redacted:

```json
{
  "status": "ok",
  "service": "cornerstones",
  "version": "0.4.1",
  "authenticated_user": "[REDACTED_SUBJECT]",
  "key_id": "[REDACTED_KEY_ID]"
}
```

If the key is missing or invalid, the command exits non-zero and prints a JSON error.

## Feature discovery

`guide` and `changelog` are customer-safe discovery surfaces owned by the server.

```bash
cornerstones-client guide
cornerstones-client changelog
```

`guide` returns product structure and contract semantics. Example excerpt:

```json
{
  "product": "cornerstones",
  "version": "0.4.1",
  "mode": "agent_feature_discovery",
  "recommended_start": [
    "GET /v1/features",
    "GET /v1/changelog",
    "cornerstones guide",
    "cornerstones context overview"
  ],
  "contract_rules": {
    "must_check": ["provenance", "degraded", "fallback", "not_implemented"],
    "semantics": {
      "degraded": "contract still holds but quality, completeness, or freshness is reduced",
      "fallback": "non-null means a degraded or alternate path was used",
      "not_implemented": "surface exists but is not fully live yet"
    }
  }
}
```

## FX and currency-pair data

Use the `fx` command group for raw or derived currency-pair data.

Supported examples include:

- `EURUSD`
- `GBPUSD`
- `USDJPY`
- `AUDUSD`
- `USDCAD`
- `USDCHF`
- `NZDUSD`
- `XAUUSD`

### Latest quote

```bash
cornerstones-client fx quote --symbol EURUSD
```

Real example:

```json
{
  "quote": {
    "symbol": "EURUSD",
    "bid": 1.17119,
    "ask": 1.17123,
    "mid": 1.17121,
    "timestamp": "2026-04-28T07:10:15+01:00",
    "freshness_status": "fresh",
    "market_state": "open",
    "provenance": "mt5",
    "degraded": false
  },
  "provenance": "mt5",
  "degraded": false,
  "message": "MT5 realtime quote"
}
```

### Candlestick bars

```bash
cornerstones-client fx bars --symbol EURUSD --timeframe 1h --count 2
```

Real example:

```json
{
  "symbol": "EURUSD",
  "timeframe": "1h",
  "bars": [
    {
      "open": 1.17083,
      "high": 1.17178,
      "low": 1.17080,
      "close": 1.17132,
      "volume": 2386,
      "timestamp": "2026-04-28T07:00:00+01:00",
      "provenance": "mt5",
      "degraded": false
    },
    {
      "open": 1.17132,
      "high": 1.17135,
      "low": 1.17116,
      "close": 1.17119,
      "volume": 386,
      "timestamp": "2026-04-28T08:00:00+01:00",
      "provenance": "mt5",
      "degraded": false
    }
  ],
  "count": 2,
  "provenance": "mt5",
  "degraded": false,
  "message": "MT5 realtime candlesticks"
}
```

### Technical indicators

```bash
cornerstones-client fx indicators --symbol USDJPY --timeframe H1 --bars 50
```

Real example:

```json
{
  "symbol": "USDJPY",
  "timeframe": "H1",
  "bars_count": 50,
  "as_of": "2026-04-28T07:00:00Z",
  "price_summary": {
    "last": 159.063,
    "high_20": 159.567,
    "low_20": 158.979
  },
  "indicators": {
    "ema_20": 159.3380132108557,
    "ema_50": 159.41626,
    "rsi_14": 35.45786404794511,
    "adx": 23.528435653585596,
    "atr_14": 0.14205550970288158,
    "vwap": 159.4171532556045
  },
  "provenance": "mt5",
  "degraded": false,
  "fallback": null,
  "message": "FX indicators derived from mt5 bars (50/50)"
}
```

### Session state

```bash
cornerstones-client fx session --symbol GBPUSD --timeframe H1 --bars 50
```

Real example:

```json
{
  "symbol": "GBPUSD",
  "timeframe": "H1",
  "bars_count": 50,
  "session_name": "asia",
  "is_session_open": true,
  "session_window": {
    "start": "00:00Z",
    "end": "07:00Z",
    "timezone": "UTC"
  },
  "range_today": 0.00185,
  "today_session_high": 1.35411,
  "today_session_low": 1.35226,
  "last_price": 1.3529,
  "provenance": "mt5",
  "degraded": false,
  "fallback": null,
  "message": "FX session state derived from mt5 bars (50/50)"
}
```

## Market context packages

Use `context` when you want a packaged view, not only raw quote/bars.

Context responses commonly include:

- `context_type`
- `context`
- `provenance`
- `data_quality`
- `degraded`
- `fallback`
- `message`

### FX context

```bash
cornerstones-client context fx --symbol XAUUSD --timeframe 1h --count 2
```

Real example:

```json
{
  "context_type": "fx",
  "provenance": "mt5+adanos",
  "degraded": false,
  "fallback": null,
  "message": "FX agent context [mt5+adanos]",
  "context": {
    "symbol": "XAUUSD",
    "quote": {
      "symbol": "XAUUSD",
      "bid": 4668.22,
      "ask": 4668.79,
      "mid": 4668.505,
      "freshness_status": "fresh",
      "market_state": "open",
      "provenance": "mt5",
      "degraded": false
    },
    "recent_bars_count": 2
  }
}
```

For non-gold FX pairs such as `EURUSD`, quote and bars can be healthy while optional sentiment or narrative sources are empty. That may appear as `fallback: {"sentiment": "source_empty"}` on context responses. Treat quote/bars as the primary currency-pair truth; treat sentiment/narrative as optional enrichment.

### Gold context

```bash
cornerstones-client context gold --symbol XAUUSD --timeframe 1h --count 2
```

Real example:

```json
{
  "context": {
    "timestamp": "2026-04-28T04:10:21.395346Z"
  },
  "provenance": "mt5+fmp+fmp+fmp+adanos",
  "degraded": false,
  "message": "Multi-provider gold context [mt5+fmp+fmp+fmp+adanos]"
}
```

### Stocks context

```bash
cornerstones-client context stocks --symbol AAPL --timeframe 1d --count 2
```

Real example excerpt:

```json
{
  "context": {
    "symbol": "AAPL",
    "quote": {
      "available": true,
      "data": {
        "symbol": "AAPL",
        "bid": 267.583239,
        "ask": 267.636761,
        "mid": 267.61,
        "provenance": "fmp",
        "degraded": false
      },
      "provenance": "fmp",
      "degraded": false,
      "message": "FMP realtime quote"
    }
  },
  "data_quality": {
    "requested_symbol": "AAPL",
    "available_components": ["quote", "profile", "bars"],
    "core_missing_components": [],
    "core_degraded_components": [],
    "coverage_ratio": 1.0
  },
  "degraded": false,
  "message": "Deterministic stocks context package for AAPL (coverage=5/5)"
}
```

`orderflow` and `imbalance` can be listed as unavailable supplementary components without making the stock context degraded. Core quote/profile/bars are the main customer-facing stock context contract.

## Order-flow surfaces

Order-flow is exposed as read-only data for XAUUSD/GC-style microstructure consumers. Admin collection/job endpoints remain server/operator-only.

```bash
cornerstones-client orderflow summary --symbol XAUUSD
cornerstones-client orderflow context --symbol XAUUSD
cornerstones-client orderflow raw --symbol XAUUSD
cornerstones-client orderflow historical --symbol XAUUSD
cornerstones-client orderflow liquidity-metrics --symbol XAUUSD
```

Real `summary` example excerpt:

```json
{
  "data": {
    "symbol": "XAUUSD",
    "futures_symbol": "GC",
    "exchange": "COMEX",
    "mode": "live",
    "summary": {
      "book_pressure_direction": "buy",
      "book_pressure_strength": "strong",
      "trade_aggression_bias": "buyer_aggressive",
      "microstructure_state": "trend_supportive",
      "session_liquidity_regime": "thin",
      "delta_persistence": "persistent_buying",
      "imbalance_persistence": "persistent_bid"
    },
    "readiness": {
      "support_only": false,
      "confirmation_only": true,
      "directional_candidate_ok": false,
      "production_ready": false
    },
    "provenance": "cornerstones+rithmic",
    "degraded": false
  }
}
```

Real `liquidity-metrics` example excerpt:

```json
{
  "data": {
    "symbol": "XAUUSD",
    "futures_symbol": "GC",
    "metrics": {
      "breakout_acceptance_score": 0.85,
      "sweep_confirmation": "not_applicable",
      "reclaim_quality": "clean",
      "post_break_acceptance": "accepted",
      "trap_probability_bucket": "unclear"
    },
    "provenance": "cornerstones+rithmic",
    "degraded": false
  }
}
```

## Chart rendering

Charts render server-side artifacts and return JSON metadata plus artifact URLs. Use the returned `image_url`, `html_url`, or `manifest_url` with the same authenticated API host.

```bash
cornerstones-client chart fx --symbol XAUUSD --timeframe H1 --bars 80 --width 900 --height 600
cornerstones-client chart stocks --symbol AAPL --timeframe 1d --bars 80 --width 900 --height 600
```

Real FX chart example excerpt:

```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "bars_count": 80,
  "engine": "tradingview_widget_local",
  "image_url": "/v1/charting/artifacts/fx_XAUUSD_H1_80_1777352081678.png",
  "html_url": "/v1/charting/artifacts/fx_XAUUSD_H1_80_1777352081678.html",
  "manifest_url": "/v1/charting/artifacts/fx_XAUUSD_H1_80_1777352081678.manifest.json",
  "image_width": 900,
  "image_height": 600,
  "indicators": ["ema20", "ema50", "rsi", "macd"],
  "provenance": "cornerstones_chart_local",
  "degraded": false,
  "fallback": null,
  "message": "Local TradingView widget chart rendered"
}
```

Stock charts can return `degraded: true` when a companion component is unavailable while the artifact still renders. Treat chart metadata like other Cornerstones payloads: inspect `degraded` and `fallback`.

## Evidence feed

Evidence feed returns live-backed raw evidence assembled from alert-store items. It is not a fabricated sentiment aggregate.

```bash
cornerstones-client evidence feed --asset XAUUSD --limit 2
```

Real example:

```json
{
  "items": [
    {
      "id": "alt_6965a5cb7378",
      "type": "alert",
      "timestamp": "2026-04-28T02:59:16.236137Z",
      "asset": "XAUUSD",
      "trigger": {
        "summary": "BoJ Interest Rate Decision (JP) - LIVE",
        "why": [
          "High-impact event 'BoJ Interest Rate Decision' in 0 minutes (milestone: LIVE)",
          "Country: JP",
          "Forecast: 0.75, Previous: 0.75"
        ],
        "lane": "scheduled_macro",
        "kind": "macro_event_milestone",
        "confirmation_status": "single_source"
      },
      "priority": "critical",
      "confidence": 0.92,
      "active": true,
      "provenance": "alerts_store",
      "degraded": false,
      "not_implemented": false
    }
  ],
  "count": 2,
  "provenance": "alerts_store",
  "degraded": false,
  "not_implemented": false,
  "message": "Evidence feed assembled from live alerts store raw evidence. No sentiment aggregation performed."
}
```

## Alerts status surfaces

The client exposes read-only alert status surfaces for customers and operators.

### Metrics

```bash
cornerstones-client alerts metrics
```

Real example excerpt:

```json
{
  "subscriptions": {
    "active": 1,
    "deleted": 0,
    "created_total": 58,
    "deleted_total": 55
  },
  "alerts": {
    "stored": 157,
    "active": 4,
    "generated_total": 580,
    "queued_total": 663,
    "by_lane": {
      "scheduled_macro": 157
    }
  },
  "deliveries": {
    "stored": 157,
    "status": {
      "queued": 0,
      "delivering": 0,
      "delivered": 157,
      "failed": 0,
      "dead_letter": 0
    }
  }
}
```

### Recent alerts

```bash
cornerstones-client alerts recent --limit 2
```

Example when no recent active alerts match the cursor:

```json
{
  "alerts": [],
  "count": 0,
  "next_cursor": null,
  "has_more": false
}
```

### Dead-letter queue

```bash
cornerstones-client alerts dead-letter --limit 2
```

Healthy empty example:

```json
{
  "deliveries": [],
  "count": 0,
  "next_cursor": null,
  "has_more": false
}
```

## Trial commands

Trial commands are onboarding helpers. They are limited-scope and may not grant access to all authenticated market surfaces.

```bash
cornerstones-client trial start
cornerstones-client trial status
cornerstones-client trial token
```

`guide` and `changelog` can use a cached trial token when no full API key is configured. `verify`, `fx`, `context`, `orderflow`, `chart`, `evidence`, and `alerts` require a real issued API key.

## Command reference

| Command | Auth | Purpose |
|---|---:|---|
| `auth status` | No | Show local client config state |
| `auth login --api-key ...` | No | Store an issued API key locally |
| `auth logout` | No | Remove stored API key |
| `auth set-base-url --base-url ...` | No | Override product portal URL |
| `auth set-api-base-url --api-base-url ...` | No | Override Core API URL |
| `trial start` | No | Start limited anonymous trial session |
| `trial status` | Trial | Check limited trial state |
| `trial token` | Trial | Mint/cache short-lived discovery token |
| `guide` | API key or trial token | Fetch product discovery guide |
| `changelog` | API key or trial token | Fetch customer-safe changelog preview |
| `verify` | API key | Verify authenticated `/v1/status` |
| `fx quote --symbol EURUSD` | API key | Fetch latest FX quote |
| `fx bars --symbol EURUSD --timeframe 1h --count 50` | API key | Fetch FX bars |
| `fx indicators --symbol USDJPY --timeframe H1 --bars 200` | API key | Fetch derived indicators |
| `fx session --symbol GBPUSD --timeframe H1 --bars 200` | API key | Fetch session state |
| `context fx --symbol XAUUSD --timeframe 1h --count 3` | API key | Fetch packaged FX context |
| `context gold --symbol XAUUSD --timeframe 1h --count 3` | API key | Fetch packaged gold context |
| `context stocks --symbol AAPL --timeframe 1d --count 3` | API key | Fetch packaged stock context |
| `orderflow summary --symbol XAUUSD` | API key | Fetch order-flow summary |
| `orderflow context --symbol XAUUSD` | API key | Fetch order-flow context |
| `orderflow raw --symbol XAUUSD` | API key | Fetch raw/latest order-flow payload |
| `orderflow historical --symbol XAUUSD` | API key | Fetch historical order-flow payload |
| `orderflow liquidity-metrics --symbol XAUUSD` | API key | Fetch liquidity metrics |
| `chart fx --symbol XAUUSD --timeframe H1 --bars 120` | API key | Render FX chart artifact |
| `chart stocks --symbol AAPL --timeframe 1d --bars 120` | API key | Render stock chart artifact |
| `evidence feed --asset XAUUSD --limit 5` | API key | Fetch live-backed evidence items |
| `alerts metrics` | API key | Fetch alert system metrics |
| `alerts recent --limit 5` | API key | Fetch recent alerts |
| `alerts dead-letter --limit 5` | API key | Fetch dead-letter deliveries |

Run built-in help for exact flags:

```bash
cornerstones-client --help
cornerstones-client fx --help
cornerstones-client context --help
cornerstones-client stocks --help
cornerstones-client options --help
cornerstones-client crypto --help
cornerstones-client macro --help
cornerstones-client geopolitics --help
cornerstones-client polymarket --help
cornerstones-client events --help
cornerstones-client cross-asset --help
cornerstones-client orderflow --help
cornerstones-client chart --help
cornerstones-client evidence --help
cornerstones-client alerts --help
```

Additional non-admin read groups exposed in `0.1.7`:

```bash
cornerstones-client crypto quote --symbol BTCUSDT
cornerstones-client stocks quote --symbol AAPL
cornerstones-client stocks screener --limit 25
cornerstones-client options chain --symbol AAPL --max-expirations 1
cornerstones-client macro summary
cornerstones-client macro calendar --country US --importance high
cornerstones-client geopolitics status
cornerstones-client geopolitics osint-feed --limit 20
cornerstones-client polymarket overview
cornerstones-client events recent --limit 20
cornerstones-client cross-asset
```

Mutation/operator surfaces remain excluded from the public client even when they are not under `/admin`: alert subscribe/dispatch/replay/resolve/test, event subscribe/receipt submission/export, evidence subscribe, geopolitics watchlist mutation/refresh, and order-flow collection jobs.

## Core API vs client alignment

The managed Cornerstones Core API currently exposes many more endpoints than this client. The client is aligned to the **customer-safe read path** rather than every operator/internal surface.

| Core API area | Client coverage | Notes |
|---|---|---|
| `/v1/status` | `verify` | Authenticated status check |
| `/v1/features` | `guide` | Discovery surface |
| `/v1/changelog` | `changelog` | Customer-safe changelog preview |
| `/v1/fx/quote` | `fx quote` | Currency-pair quote |
| `/v1/fx/bars` | `fx bars` | Currency-pair bars |
| `/v1/fx/indicators` | `fx indicators` | Derived indicators |
| `/v1/fx/session` | `fx session` | Session state |
| `/v1/context/fx` | `context fx` | Packaged FX context |
| `/v1/gold/context` | `context gold` | Packaged gold context |
| `/v1/stocks/context` | `context stocks` | Packaged stock context |
| `/v1/orderflow/summary` | `orderflow summary` | Read-only order-flow summary |
| `/v1/orderflow/context` | `orderflow context` | Read-only order-flow context |
| `/v1/orderflow/raw` | `orderflow raw` | Raw/latest order-flow payload |
| `/v1/orderflow/historical` | `orderflow historical` | Historical order-flow payload |
| `/v1/orderflow/liquidity-metrics` | `orderflow liquidity-metrics` | Liquidity metrics |
| `/v1/fx/chart` | `chart fx` | FX chart artifact metadata |
| `/v1/stocks/chart` | `chart stocks` | Stock chart artifact metadata |
| `/v1/evidence/feed` | `evidence feed` | Live-backed evidence feed |
| `/v1/alerts/metrics` | `alerts metrics` | Read-only alert metrics |
| `/v1/alerts/recent` | `alerts recent` | Read-only recent alerts |
| `/v1/alerts/dead-letter` | `alerts dead-letter` | Read-only dead-letter queue |

Not exposed by the client on purpose:

- admin and operator endpoints
- order-flow collection jobs / maintenance mutations
- subscription creation/deletion
- alert dispatch/replay/resolve/test mutation flows
- internal maintenance endpoints
- artifact binary download helpers beyond returned chart URLs
- advanced direct domain surfaces that are still best consumed through server-owned discovery docs or a custom integration

For enterprise integrations that need lower-level API access, use the Core API directly with the issued API key and inspect `guide` for contract semantics.

## Response contract: fields to check

Every downstream agent or customer integration should inspect these fields when present:

| Field | Meaning |
|---|---|
| `provenance` | Where the data came from, e.g. `mt5`, `fmp`, `alerts_store` |
| `degraded` | `true` means response contract still holds, but quality/completeness/freshness is reduced |
| `fallback` | Non-null means an alternate or degraded path was used |
| `not_implemented` | Surface exists but is not fully live yet |
| `data_quality` | Structured quality and coverage details, when available |

A response can return HTTP 200 and still be `degraded: true`. That is intentional: the transport succeeded, but the data quality signal says downstream systems should use caution.

## Security notes

- Do not paste API keys into shared chats, tickets, screenshots, or logs.
- Prefer environment variables or a local secret manager when automating `auth login`.
- Redact `api_key`, `key_id`, `Authorization`, `Cookie`, and any webhook targets in customer support output.
- `cornerstones-client` stores credentials locally; protect the host account that runs it.

## Development and release verification

Source install:

```bash
git clone https://github.com/luxiaolei/cornerstones-client.git
cd cornerstones-client
python -m pip install -e '.[dev]'
pytest -q
```

Build and package check:

```bash
python -m build
python -m twine check dist/*
```

Release runbook:

- `docs/release/first-publication-runbook.md`

## Disclaimer

Cornerstones provides market data and context surfaces for analysis workflows. It does not provide financial advice, investment recommendations, or trade execution guarantees.
