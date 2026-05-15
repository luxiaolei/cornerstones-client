# Cornerstones Client CLI Reference

Machine-readable customer CLI reference for `cornerstones-client==0.1.19`.

## Install

```bash
python -m pip install -U cornerstones-client==0.1.19
```

## Auth/config

Config file: `~/.config/cornerstones-client/config.json`.

```bash
cornerstones-client auth status
cornerstones-client auth login --api-key <issued-api-key>
cornerstones-client auth logout
cornerstones-client auth set-base-url --base-url https://www.usecornerstones.com
cornerstones-client auth set-api-base-url --api-base-url https://api.usecornerstones.com
```

## Access matrix

- Trial/no-key: discovery-only (`guide`, `changelog`, `/v1/features`, `/v1/changelog`).
- Free API key: 500 requests/month, 10 requests/minute, basic authenticated market truth only.
- Pro API key: adds charts, Layer 5 context, options, macro exact series, and event export.
- Max API key: adds orderflow raw/summary/context/historical and liquidity metrics.

`verify` always requires a real issued API key. `chart fx` and `chart stocks` are Pro+. All `orderflow ...` commands are Max-only.
Stock research inputs such as transcripts, analyst estimates, ratings, price targets, ratios, and key metrics are authenticated read-only API-key surfaces.

## Command catalog with example outputs

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

### `fx options-proxy`

Command:

```bash
cornerstones-client fx options-proxy --symbol EURUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"EURUSD","proxy":true,"experimental":true,"proxy_symbols":["FXE"],"proxy_formula":"FXE ETF options as support-only EURUSD volatility proxy; not OTC FX options truth","trust_tier":"support","usage_hint":"support_input","primary_input_allowed":false,"native_otc_fx_options_available":false,"components":[{"proxy_symbol":"FXE","role":"euro_etf_options","analysis":{},"degraded":false}],"provenance":"options_service","degraded":false,"data_quality":{"support_only":true,"component_count":1}}
```

### `fx positioning`

Command:

```bash
cornerstones-client fx positioning --symbol EURUSD
```

Example output (redacted / shape-preserving):

```json
{"symbol":"EURUSD","proxy":true,"experimental":true,"trust_tier":"shadow","usage_hint":"shadow_only","primary_input_allowed":false,"components":{"cot":{"available":false,"status":"provider_missing","usage_hint":"do_not_use"},"futures_oi":{"available":false,"status":"provider_missing","usage_hint":"do_not_use"},"retail_positioning":{"available":false,"status":"provider_missing","usage_hint":"do_not_use"},"broker_flow":{"available":false,"status":"provider_missing","usage_hint":"do_not_use"}},"provenance":"none","degraded":false,"fallback":"positioning_providers_missing","data_quality":{"neutral_positioning_inferred":false}}
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

A-share phase 1 uses existing `/v1/stocks/*` endpoints with FMP provider contracts:

- Shanghai A-shares: symbol suffix `.SS`, screener exchange `SHH` (example `600519.SS`).
- Shenzhen A-shares: symbol suffix `.SZ`, screener exchange `SHZ` (example `000001.SZ`).
- `.SH` user input can be normalized to `.SS` via `stocks normalize-symbol`.
- `.BJ` / Beijing Stock Exchange is explicitly unsupported in current phase; planned for future China-market coverage.

### `stocks quote`

Command:

```bash
cornerstones-client stocks quote --symbol AAPL
cornerstones-client stocks quote --symbol 600519.SS
cornerstones-client stocks quote --symbol 000001.SZ
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


### `stocks normalize-symbol`

Command:

```bash
cornerstones-client stocks normalize-symbol --symbol 600519.SH
```

Example output (redacted / shape-preserving):

```json
{"raw_symbol":"600519.SH","canonical_symbol":"600519.SS","provider_symbol":"600519.SS","market":"china_shanghai","exchange_code":"SHH","supported":true,"normalized":true}
```

### `stocks exchanges`

Command:

```bash
cornerstones-client stocks exchanges
```

Example output (redacted / shape-preserving):

```json
{"exchanges":[{"code":"SHH","symbol_suffix":".SS","supported":true},{"code":"SHZ","symbol_suffix":".SZ","supported":true},{"code":"BSE","symbol_suffix":".BJ","supported":false}]}
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
cornerstones-client stocks filings --symbol AAPL --provider sec --form 10-Q --limit 3
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","provider":"sec","count":3,"filings":[{"form":"10-Q","filing_date":"2026-04-25","accession_number":"0000320193-26-000001","primary_document_url":"https://www.sec.gov/..."}],"degraded":false}
```

### `stocks facts`

Command:

```bash
cornerstones-client stocks facts --symbol AAPL --period annual --limit 4
```

Example output (redacted / shape-preserving):

```json
{"symbol":"AAPL","provider":"sec","period":"annual","facts":[{"concept":"Revenues","value":391035000000,"unit":"USD","period_end":"2025-09-27"}],"degraded":false}
```

Note: live SEC reads require Core runtime `CORNERSTONES_SEC_USER_AGENT` with operator contact. Missing identity degrades safely instead of calling SEC.

### `stocks transcripts`

Command:

```bash
cornerstones-client stocks transcripts --symbol AAPL --year 2025 --quarter 4 --limit 1 --include-text
```

### `stocks analyst-estimates`

Command:

```bash
cornerstones-client stocks analyst-estimates --symbol AAPL --period quarter --limit 6 --from 2025-01-01 --to 2026-01-01
```

### `stocks ratings`

Command:

```bash
cornerstones-client stocks ratings --symbol AAPL --limit 7 --from 2025-01-01 --to 2026-01-01
```

### `stocks price-targets`

Command:

```bash
cornerstones-client stocks price-targets --symbol AAPL --limit 8 --from 2025-01-01 --to 2026-01-01 --include-consensus
```

### `stocks ratios`

Command:

```bash
cornerstones-client stocks ratios --symbol AAPL --period ttm --limit 5
```

### `stocks key-metrics`

Command:

```bash
cornerstones-client stocks key-metrics --symbol AAPL --period annual --limit 5
```

### `stocks research-context`

Command:

```bash
cornerstones-client stocks research-context --symbol AAPL --sections transcripts,analyst,valuation --limit-per-section 2 --include-explanations
```

These commands return neutral stock research evidence and context inputs. They do not return trading verdicts.

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
cornerstones-client stocks screener --exchange SHH --limit 25
cornerstones-client stocks screener --exchange SHZ --limit 25
```

Example output (redacted / shape-preserving):

```json
{"count":5,"rows":[{"symbol":"AAPL","marketCap":3000000000000}],"degraded":false}
```

### `stocks universe`

Command:

```bash
cornerstones-client stocks universe --preset us-stocks-liquid --limit 5
cornerstones-client stocks universe --preset china-a-shares-largecap --limit 25
```

Example output (redacted / shape-preserving):

```json
{"preset":"us-stocks-liquid","count":5,"symbols":["AAPL","MSFT","NVDA"],"degraded":false}
```

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


## Safety split

Public client exposes reads and customer-owned subscription create/delete. It excludes admin/operator/internal/destructive APIs, alert dispatch/replay/resolve/test, event receipt submit/export, order-flow jobs, and maintenance routes.
