# Cornerstones Client

`cornerstones-client` is the customer-facing CLI for the managed Cornerstones Core API.

It exposes **customer-safe read surfaces** plus **customer-owned alert/event subscription create/delete flows**. It intentionally does **not** expose admin/operator/internal/destructive flows such as alert dispatch/replay/resolve/test, event receipt submission/export, order-flow collection jobs, or maintenance jobs.

Current documented release: `0.1.13`.

## Install

```bash
python -m pip install -U cornerstones-client==0.1.13
```

Requirements:

- Python `>=3.11`
- browser trial token or issued Cornerstones API key for authenticated data
- network access to `https://api.usecornerstones.com`

## Access matrix

Trial/no-key access is discovery-only: `guide` and `changelog` can use a signed discovery token, but `verify` and market-data reads require a real issued API key. Free keys are limited to **500 requests/month** and **10 requests/minute**. Charts require **Pro+**. Orderflow requires **Max**. See `docs/ACCESS_MATRIX.md` for the canonical customer-facing matrix.

## Login

```bash
cornerstones-client auth login --api-key <issued-api-key>
cornerstones-client verify
```

Do not paste real keys into shared logs. For webhook signing secrets, use env vars:

```bash
export CLIENT_SIGNING_SECRET='...'
cornerstones-client alerts subscribe \
  --asset XAUUSD \
  --lane x_pressure \
  --webhook-url https://client.example.com/cornerstones/alerts \
  --signing-secret-env CLIENT_SIGNING_SECRET \
  --yes
```

## Full exposed command list

- `auth status`
- `auth login`
- `auth logout`
- `auth set-base-url`
- `auth set-api-base-url`
- `trial start`
- `trial status`
- `trial token`
- `guide`
- `changelog`
- `verify`
- `fx quote`
- `fx bars`
- `fx indicators`
- `fx session`
- `context fx`
- `context gold`
- `context stocks`
- `orderflow summary` (Max)
- `orderflow context` (Max)
- `orderflow raw` (Max)
- `orderflow historical` (Max)
- `orderflow liquidity-metrics` (Max)
- `chart fx` (Pro+) — returns Core-rendered artifact URLs/manifest; public output uses `cornerstones_chart_renderer` labels.
- `chart stocks` (Pro+) — supports intermarket/context bundles when Core has explicit benchmark mappings.
- `crypto quote`
- `crypto ticker`
- `crypto bars`
- `crypto indicators`
- `crypto session`
- `crypto depth`
- `crypto trades`
- `stocks quote`
- `stocks profile`
- `stocks optionability`
- `stocks context`
- `stocks indicators`
- `stocks session`
- `stocks depth`
- `stocks imbalance`
- `stocks tick`
- `stocks earnings`
- `stocks filings`
- `stocks corporate-actions`
- `stocks screener`
- `stocks universe`
- `stocks normalize-symbol`
- `stocks exchanges`
- `options chain`
- `options analysis`
- `options wall`
- `macro summary`
- `macro yields`
- `macro series`
- `macro calendar`
- `geopolitics context`
- `geopolitics status`
- `geopolitics watchlist`
- `geopolitics pizza-index`
- `geopolitics evidence`
- `geopolitics osint-feed`
- `geopolitics polymarket`
- `polymarket overview`
- `polymarket context`
- `events recent`
- `events history`
- `events receipts`
- `events subscribe`
- `events delete`
- `cross-asset`
- `evidence feed`
- `alerts metrics`
- `alerts recent`
- `alerts dead-letter`
- `alerts list`
- `alerts history`
- `alerts security-status`
- `alerts show`
- `alerts subscribe`
- `alerts delete`

## Response contract

Most commands print JSON. Common fields:

- `degraded`: `false` means required/core path was healthy. Optional upstream-empty components may still be marked `available=false` inside nested objects.
- `fallback`: present when Core API had to use fallback/degraded behavior.
- `provenance` / `data_quality`: source and freshness metadata.
- subscription responses redact secret-like fields as `[REDACTED]`.

## Full command examples

## Auth / local config

### `auth status`

Command:

```bash
cornerstones-client auth status
```

Example output (redacted / shape-preserving):

```json
{"portal_base_url":"https://www.usecornerstones.com","api_base_url":"https://api.usecornerstones.com","logged_in":true,"has_trial_cookie":false,"has_trial_token":false}
```

### `auth login`

Command:

```bash
cornerstones-client auth login --api-key <issued-api-key>
```

Example output (redacted / shape-preserving):

```json
{"logged_in":true,"api_base_url":"https://api.usecornerstones.com"}
```

### `auth logout`

Command:

```bash
cornerstones-client auth logout
```

Example output (redacted / shape-preserving):

```json
{"logged_out":true}
```

### `auth set-base-url`

Command:

```bash
cornerstones-client auth set-base-url --base-url https://www.usecornerstones.com
```

Example output (redacted / shape-preserving):

```json
{"saved":true,"portal_base_url":"https://www.usecornerstones.com"}
```

### `auth set-api-base-url`

Command:

```bash
cornerstones-client auth set-api-base-url --api-base-url https://api.usecornerstones.com
```

Example output (redacted / shape-preserving):

```json
{"saved":true,"api_base_url":"https://api.usecornerstones.com"}
```

## Trial / discovery

### `trial start`

Command:

```bash
cornerstones-client trial start
```

Example output (redacted / shape-preserving):

```json
{"trial":{"status":"active","remaining_requests":50},"token":{"expires_at":"2026-04-29T00:00:00Z"}}
```

### `trial status`

Command:

```bash
cornerstones-client trial status
```

Example output (redacted / shape-preserving):

```json
{"status":"active","remaining_requests":49,"expires_at":"2026-04-29T00:00:00Z"}
```

### `trial token`

Command:

```bash
cornerstones-client trial token
```

Example output (redacted / shape-preserving):

```json
{"token":{"token":"[REDACTED]","expires_at":"2026-04-29T00:00:00Z"}}
```

### `guide`

Command:

```bash
cornerstones-client guide
```

Example output (redacted / shape-preserving):

```json
{"product":"cornerstones","surface_count":70,"features":[{"name":"fx","status":"available"}]}
```

### `changelog`

Command:

```bash
cornerstones-client changelog
```

Example output (redacted / shape-preserving):

```json
{"versions":[{"version":"0.1.9","highlights":["complete customer CLI documentation"]}]}
```

## Verification

### `verify`

Command:

```bash
cornerstones-client verify
```

Example output (redacted / shape-preserving):

```json
{"ok":true,"authenticated":true,"plan":"admin","scopes":["read","write","admin"]}
```

## FX

### `fx quote`

Command:

```bash
cornerstones-client fx quote --symbol EURUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"EURUSD","bid":1.1609,"ask":1.1611,"mid":1.1610,"degraded":false,"provenance":"runtime"}
```

### `fx bars`

Command:

```bash
cornerstones-client fx bars --symbol EURUSD --timeframe 1h --count 3
```

Example output (redacted / shape-preserving):

```json
{"symbol":"EURUSD","timeframe":"1h","count":3,"bars":[{"time":"2026-04-28T04:00:00Z","open":1.1604,"high":1.1614,"low":1.1600,"close":1.1610}]}
```

### `fx indicators`

Command:

```bash
cornerstones-client fx indicators --symbol USDJPY --timeframe H1 --bars 50
```

Example output (redacted / shape-preserving):

```json
{"symbol":"USDJPY","timeframe":"H1","indicators":{"rsi14":54.2,"ema20":156.41},"degraded":false}
```

### `fx session`

Command:

```bash
cornerstones-client fx session --symbol XAUUSD --timeframe H1 --bars 80
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","session":"london","range":{"high":2348.2,"low":2339.1},"degraded":false}
```

## Context

### `context fx`

Command:

```bash
cornerstones-client context fx --symbol XAUUSD --timeframe 1h --count 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","context":{"quote":{},"macro":{},"correlation_evidence":{}},"degraded":false}
```

### `context gold`

Command:

```bash
cornerstones-client context gold --symbol XAUUSD --timeframe 1h --count 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","market":"gold","context":{"futures_proxy":"GC","fx_quote":{}},"degraded":false}
```

### `context stocks`

Command:

```bash
cornerstones-client context stocks --symbol AAPL --timeframe 1d --count 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","context":{"quote":{},"profile":{},"options":{}},"degraded":false}
```

## Orderflow

### `orderflow summary`

Command:

```bash
cornerstones-client orderflow summary --symbol XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","summary":{"bias":"neutral","liquidity_score":0.62},"degraded":false}
```

### `orderflow context`

Command:

```bash
cornerstones-client orderflow context --symbol XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","context":{"delta":{},"liquidity":{}},"degraded":false}
```

### `orderflow raw`

Command:

```bash
cornerstones-client orderflow raw --symbol XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","snapshot":{"bids":[],"asks":[]},"degraded":false}
```

### `orderflow historical`

Command:

```bash
cornerstones-client orderflow historical --symbol XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","count":20,"items":[{"asof":"2026-04-28T04:00:00Z","imbalance":0.08}]}
```

### `orderflow liquidity-metrics`

Command:

```bash
cornerstones-client orderflow liquidity-metrics --symbol XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","liquidity_metrics":{"spread":0.2,"depth_score":0.71},"degraded":false}
```

## Chart

### `chart fx`

Command:

```bash
cornerstones-client chart fx --symbol XAUUSD --timeframe H1 --bars 120 --indicator rsi
```

Example output (redacted / shape-preserving):

```json
{"symbol":"XAUUSD","engine":"cornerstones_chart_renderer","image_url":"https://api.usecornerstones.com/artifacts/chart_xxx.png","manifest_url":"https://api.usecornerstones.com/artifacts/chart_xxx.json","degraded":false}
```

### `chart stocks`

Command:

```bash
cornerstones-client chart stocks --symbol AAPL --timeframe 1d --bars 80
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","engine":"cornerstones_chart_renderer","image_url":"https://api.usecornerstones.com/artifacts/chart_xxx.png","degraded":false,"warnings":[]}
```

## Crypto

### `crypto quote`

Command:

```bash
cornerstones-client crypto quote --symbol BTCUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","bid":94480.1,"ask":94491.2,"mid":94485.6,"degraded":false}
```

### `crypto ticker`

Command:

```bash
cornerstones-client crypto ticker --symbol BTCUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","last":94485.6,"volume_24h":12345.0,"degraded":false}
```

### `crypto bars`

Command:

```bash
cornerstones-client crypto bars --symbol BTCUSD --timeframe 1h --count 3
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","timeframe":"1h","count":3,"bars":[{"time":"2026-04-28T04:00:00Z","close":94485.6}]}
```

### `crypto indicators`

Command:

```bash
cornerstones-client crypto indicators --symbol BTCUSD --timeframe 1h --bars 50
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","indicators":{"rsi14":51.8,"ema20":94210.4},"degraded":false}
```

### `crypto session`

Command:

```bash
cornerstones-client crypto session --symbol BTCUSD --timeframe 1h --bars 80
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","session":"global","range":{"high":95120.0,"low":93880.5},"degraded":false}
```

### `crypto depth`

Command:

```bash
cornerstones-client crypto depth --symbol BTCUSD --limit 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","bids":[[94480.0,1.2]],"asks":[[94491.0,0.9]],"degraded":false}
```

### `crypto trades`

Command:

```bash
cornerstones-client crypto trades --symbol BTCUSD --limit 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"BTCUSD","trades":[{"price":94485.6,"size":0.12,"side":"buy"}],"degraded":false}
```

## Stocks

### `stocks quote`

Command:

```bash
cornerstones-client stocks quote --symbol AAPL
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","price":214.7,"currency":"USD","degraded":false,"provenance":"ib"}
```

### `stocks profile`

Command:

```bash
cornerstones-client stocks profile --symbol AAPL
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","company_name":"Apple Inc.","exchange":"NASDAQ","sector":"Technology"}
```

### `stocks optionability`

Command:

```bash
cornerstones-client stocks optionability --symbol AAPL
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","optionable":true,"degraded":false,"reason":null}
```

### `stocks context`

Command:

```bash
cornerstones-client stocks context --symbol AAPL --bars-count 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","context":{"quote":{},"profile":{},"optionability":{}},"degraded":false}
```

### `stocks indicators`

Command:

```bash
cornerstones-client stocks indicators --symbol AAPL --timeframe 1d --bars 80
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","timeframe":"1d","indicators":{"rsi14":57.3,"sma20":211.4},"degraded":false}
```

### `stocks session`

Command:

```bash
cornerstones-client stocks session --symbol AAPL --timeframe 1d --bars 80
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","session":"regular","range":{"high":216.2,"low":212.5},"degraded":false}
```

### `stocks depth`

Command:

```bash
cornerstones-client stocks depth --symbol AAPL --num-rows 5
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","rows":[{"bid":214.68,"ask":214.72,"bid_size":100,"ask_size":100}],"degraded":false}
```

### `stocks imbalance`

Command:

```bash
cornerstones-client stocks imbalance --symbol AAPL --exchange NYSE
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","exchange":"NYSE","imbalance":null,"degraded":false,"available":false}
```

### `stocks tick`

Command:

```bash
cornerstones-client stocks tick --symbol AAPL --tick-type Last --num-ticks 10
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","tick_type":"Last","ticks":[{"time":"2026-04-28T13:30:01Z","price":214.7}]}
```

### `stocks earnings`

Command:

```bash
cornerstones-client stocks earnings --symbol AAPL --from 2026-04-01 --to 2026-06-30
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","count":1,"events":[{"date":"2026-05-01","status":"confirmed"}],"degraded":false}
```

### `stocks filings`

Command:

```bash
cornerstones-client stocks filings --symbol AAPL --form 10-Q --limit 3
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","count":3,"filings":[{"form":"10-Q","filed_at":"2026-04-25","url":"https://www.sec.gov/..."}]}
```

### `stocks corporate-actions`

Command:

```bash
cornerstones-client stocks corporate-actions --symbol AAPL --type all
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","actions":[{"type":"dividend","ex_date":"2026-05-10"}],"degraded":false}
```

### `stocks screener`

Command:

```bash
cornerstones-client stocks screener --market-cap-more-than 10000000000 --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":5,"rows":[{"symbol":"AAPL","marketCap":3000000000000}],"degraded":false}
```

### `stocks universe`

Command:

```bash
cornerstones-client stocks universe --preset us-stocks-liquid --limit 5
```

Example output (redacted / shape-preserving):

```json
{"preset":"us-stocks-liquid","count":5,"symbols":["AAPL","MSFT","NVDA"],"degraded":false}
```

### China A-share examples

Current A-share support uses provider-native suffixes and exchange codes:

```bash
cornerstones-client stocks quote --symbol 600519.SS
cornerstones-client stocks quote --symbol 000001.SZ
cornerstones-client stocks screener --exchange SHH --limit 25
cornerstones-client stocks screener --exchange SHZ --limit 25
cornerstones-client stocks universe --preset china-a-shares-largecap --limit 25
cornerstones-client stocks normalize-symbol --symbol 600519.SH
cornerstones-client stocks exchanges
```

Contracts:

- Shanghai quote/profile/bars symbols use `.SS`; `.SH` is normalized to `.SS` by Core.
- Shenzhen quote/profile/bars symbols use `.SZ`.
- Screener exchange codes are `SHH` and `SHZ`.
- Beijing/BSE `.BJ` is explicitly unsupported in the current public phase; later China-specific enrichment can add BJ metadata and adjusted bars.

## Options

Options are read-only market-truth surfaces. Cornerstones/client expose chain, wall, and analysis data only; they do not expose BAG/ComboLeg construction, what-if, order submit/cancel, risk, or reconciliation.

### `options chain`

Command:

```bash
cornerstones-client options chain --symbol AAPL --max-expirations 1 --include quote,greeks,oi,volume,iv
```

Aliases:

- `--expiration` and `--expiration-date`

Example output (redacted / shape-preserving):

```json
{"chain":{"underlying_symbol":"AAPL","sec_type":"OPT","underlying_type":"STK","total_contracts":12,"quality_metadata":{"contract_count":12,"contracts_with_bid_ask":10,"contracts_with_greeks":8,"contracts_with_volume":6,"contracts_with_open_interest":12},"contracts":[{"sec_type":"OPT","option_type":"call","strike":215.0,"expiration_date":"2026-05-15T00:00:00","underlying_type":"STK","has_bid_ask":true,"has_mid":true,"has_greeks":true,"has_volume":true,"has_open_interest":true}],"degraded":false,"provenance":"cornerstones_options_primary"},"provenance":"cornerstones_options_primary","degraded":false,"fallback":null}
```

### `options analysis`

Command:

```bash
cornerstones-client options analysis --symbol AAPL --expiration 2026-05-15
```

Example output (redacted / shape-preserving):

```json
{"analysis":{"underlying_symbol":"AAPL","put_call_ratio":2.506,"max_pain_strike":265.0,"degraded":false,"provenance":"cornerstones_options_primary","data_quality":{"chain_quality":{"contract_count":12,"contracts_with_greeks":8}}},"message":"Options analysis for AAPL"}
```

### `options wall`

Command:

```bash
cornerstones-client options wall --symbol AAPL --threshold 90
```

Aliases:

- `--threshold` and `--threshold-percentile`
- `--expiration` and `--expiration-date`

Example output (redacted / shape-preserving):

```json
{"wall":{"underlying_symbol":"AAPL","call_walls":[{"strike":250.0,"open_interest":1200,"volume":300,"percentile":95.0}],"put_walls":[],"degraded":false,"provenance":"cornerstones_options_primary","data_quality":{"wall_metric":"open_interest","has_open_interest_data":true}},"message":"Options wall analysis for AAPL"}
```

## Macro

### `macro summary`

Command:

```bash
cornerstones-client macro summary
```

Example output (redacted / shape-preserving):

```json
{"summary":{"risk_calendar":"normal","next_high_importance_event":"FOMC"},"degraded":false}
```

### `macro yields`

Command:

```bash
cornerstones-client macro yields
```

Example output (redacted / shape-preserving):

```json
{"curves":{"US10Y":4.62,"US2Y":4.91},"degraded":false}
```

### `macro series`

Command:

```bash
cornerstones-client macro series --name dxy
```

Example output (redacted / shape-preserving):

```json
{"name":"dxy","count":100,"observations":[{"time":"2026-04-28","value":105.2}],"degraded":false}
```

### `macro calendar`

Command:

```bash
cornerstones-client macro calendar --country US --importance high
```

Example output (redacted / shape-preserving):

```json
{"count":3,"events":[{"time":"2026-04-30T12:30:00Z","country":"US","event":"GDP","importance":"high"}]}
```

## Geopolitics / OSINT

### `geopolitics context`

Command:

```bash
cornerstones-client geopolitics context
```

Example output (redacted / shape-preserving):

```json
{"context":{"risk_level":"medium","drivers":[]},"degraded":false}
```

### `geopolitics status`

Command:

```bash
cornerstones-client geopolitics status
```

Example output (redacted / shape-preserving):

```json
{"status":"ok","feeds":{"osint":"available","pizza_index":"available"},"degraded":false}
```

### `geopolitics watchlist`

Command:

```bash
cornerstones-client geopolitics watchlist
```

Example output (redacted / shape-preserving):

```json
{"watchlist":[{"region":"Middle East","priority":"medium"}],"degraded":false}
```

### `geopolitics pizza-index`

Command:

```bash
cornerstones-client geopolitics pizza-index
```

Example output (redacted / shape-preserving):

```json
{"pizza_index":{"status":"normal","signal":"baseline"},"degraded":false}
```

### `geopolitics evidence`

Command:

```bash
cornerstones-client geopolitics evidence --min-priority medium
```

Example output (redacted / shape-preserving):

```json
{"count":5,"evidence":[{"priority":"medium","summary":"..."}],"degraded":false}
```

### `geopolitics osint-feed`

Command:

```bash
cornerstones-client geopolitics osint-feed --limit 5 --min-priority medium
```

Example output (redacted / shape-preserving):

```json
{"count":5,"items":[{"source":"osint","priority":"medium","headline":"..."}],"degraded":false}
```

### `geopolitics polymarket`

Command:

```bash
cornerstones-client geopolitics polymarket --limit 5 --keyword election
```

Example output (redacted / shape-preserving):

```json
{"count":5,"markets":[{"question":"...","probability":0.42}],"degraded":false}
```

## Polymarket

### `polymarket overview`

Command:

```bash
cornerstones-client polymarket overview
```

Example output (redacted / shape-preserving):

```json
{"overview":{"market_count":120,"top_themes":["macro","election"]},"degraded":false}
```

### `polymarket context`

Command:

```bash
cornerstones-client polymarket context
```

Example output (redacted / shape-preserving):

```json
{"context":{"markets":[],"risk_themes":[]},"degraded":false}
```

## Events

### `events recent`

Command:

```bash
cornerstones-client events recent --symbol XAUUSD --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":5,"events":[{"event_id":"evt_example","event_family":"scheduled_macro","severity":"medium","affected_symbols":["XAUUSD"]}],"degraded":false}
```

### `events history`

Command:

```bash
cornerstones-client events history --family scheduled_macro --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":5,"events":[{"event_id":"evt_example","event_family":"scheduled_macro"}],"has_more":false}
```

### `events receipts`

Command:

```bash
cornerstones-client events receipts --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":0,"receipts":[],"degraded":false}
```

### `events subscribe`

Command:

```bash
cornerstones-client events subscribe --symbol XAUUSD --family scheduled_macro --webhook-url https://client.example.com/cornerstones/events --signing-secret-env CLIENT_SIGNING_SECRET --yes
```

Example output (redacted / shape-preserving):

```json
{"subscription":{"subscription_id":"sub_example","status":"active","filters":{"symbol":"XAUUSD","family":"scheduled_macro"},"delivery":{"signing_secret":"[REDACTED]"}},"bootstrap":{"mode":"snapshot"}}
```

### `events delete`

Command:

```bash
cornerstones-client events delete --subscription-id sub_example --yes
```

Example output (redacted / shape-preserving):

```json
{"deleted":true,"subscription_id":"sub_example","status":"deleted"}
```

## Cross-asset

### `cross-asset`

Command:

```bash
cornerstones-client cross-asset
```

Example output (redacted / shape-preserving):

```json
{"context":{"fx":{},"gold":{},"stocks":{},"crypto":{},"macro":{}},"degraded":false}
```

## Evidence

### `evidence feed`

Command:

```bash
cornerstones-client evidence feed --limit 5 --asset XAUUSD
```

Example output (redacted / shape-preserving):

```json
{"count":5,"items":[{"evidence_id":"ev_example","asset":"XAUUSD","source":"alerts_store","priority":"medium"}],"degraded":false,"not_implemented":false}
```

## Alerts

### `alerts metrics`

Command:

```bash
cornerstones-client alerts metrics
```

Example output (redacted / shape-preserving):

```json
{"subscriptions":{"active":1,"total":1},"deliveries":{"dead_letter":0,"failed":0},"degraded":false}
```

### `alerts recent`

Command:

```bash
cornerstones-client alerts recent --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":3,"deliveries":[{"delivery_id":"del_example","status":"delivered","subscription_id":"sub_example"}],"degraded":false}
```

### `alerts dead-letter`

Command:

```bash
cornerstones-client alerts dead-letter --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":0,"items":[],"degraded":false}
```

### `alerts list`

Command:

```bash
cornerstones-client alerts list --status active
```

Example output (redacted / shape-preserving):

```json
{"count":1,"subscriptions":[{"subscription_id":"sub_example","status":"active","assets":["XAUUSD"]}]}
```

### `alerts history`

Command:

```bash
cornerstones-client alerts history --asset XAUUSD --limit 5
```

Example output (redacted / shape-preserving):

```json
{"count":5,"items":[{"subscription_id":"sub_example","lane":"x_pressure","lifecycle":"delivered"}]}
```

### `alerts security-status`

Command:

```bash
cornerstones-client alerts security-status --subscription-id sub_example
```

Example output (redacted / shape-preserving):

```json
{"subscription_id":"sub_example","security":{"require_signing":true,"headers_redacted":true}}
```

### `alerts show`

Command:

```bash
cornerstones-client alerts show --subscription-id sub_example
```

Example output (redacted / shape-preserving):

```json
{"subscription":{"subscription_id":"sub_example","status":"active","delivery":{"signing_secret":"[REDACTED]"}}}
```

### `alerts subscribe`

Command:

```bash
cornerstones-client alerts subscribe --asset XAUUSD --lane x_pressure --webhook-url https://client.example.com/cornerstones/alerts --signing-secret-env CLIENT_SIGNING_SECRET --yes
```

Example output (redacted / shape-preserving):

```json
{"subscription":{"subscription_id":"sub_example","status":"active","assets":["XAUUSD"],"lanes":["x_pressure"],"delivery":{"signing_secret":"[REDACTED]"}},"bootstrap":{"mode":"snapshot"}}
```

### `alerts delete`

Command:

```bash
cornerstones-client alerts delete --subscription-id sub_example --yes
```

Example output (redacted / shape-preserving):

```json
{"deleted":true,"subscription_id":"sub_example","status":"deleted"}
```


## Excluded from public client

Not exposed by design:

- admin/operator endpoints
- internal maintenance jobs
- order-flow collection/admin jobs
- alert dispatch/replay/resolve/test
- event receipt submit/export
- destructive state mutations beyond customer-owned subscription create/delete
- direct binary artifact download helpers; chart commands return artifact URLs/metadata instead

## Troubleshooting

- `not_logged_in`: run `cornerstones-client auth login --api-key <issued-api-key>`.
- `missing_signing_secret`: set env var named by `--signing-secret-env`.
- `confirmation_required`: add `--yes` for subscription create/delete.
- `401` / `403`: key missing, expired, or lacks required scope.
- `degraded=true`: inspect `fallback` and `data_quality`; this is provider/runtime truth, not a client crash.
