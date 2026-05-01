# Changelog

All notable changes to `cornerstones-client` will be documented in this file.

## Unreleased

## 0.1.10

- Added FMP-first China A-share client parity for stocks commands, including Shanghai/Shenzhen examples (`.SS`/`.SZ`), screener exchange codes (`SHH`/`SHZ`), `normalize-symbol`, and `exchanges` helper surfaces.

## 0.1.9

- Fully refreshed README and CLI reference to cover every exposed customer command with command examples and redacted/shape-preserving JSON output examples.
- Fixed subscription UX/documentation gap: alert/event subscription mutations now require `--yes`, event subscription delete is available as an alerts-backed customer subscription deletion, and comma-separated alert assets/lanes are normalized.
- Kept admin/operator/internal/destructive flows explicitly excluded from the public client docs.

## 0.1.8

- Added guarded customer subscription commands:
  - `alerts subscribe` for `/v1/alerts/subscribe`
  - `alerts delete` for `/v1/alerts/{subscription_id}` customer-owned deletion
  - `events subscribe` for `/v1/events/subscribe`
- Added shared webhook/openclaw-bridge delivery flags, metadata flags, bootstrap flags, and secret redaction for subscription responses.
- Kept admin/operator flows excluded: alert dispatch/replay/resolve/test, event receipt submission/export, order-flow jobs, and internal maintenance.

## 0.1.7

- Expanded `cornerstones-client` to cover remaining non-admin read surfaces from Core API:
  - `crypto` quote/ticker/bars/indicators/session/depth/trades
  - `stocks` quote/profile/context/indicators/session/depth/imbalance/tick/optionability/earnings/filings/corporate-actions/screener/universe
  - `options` chain/analysis/wall
  - `macro` summary/calendar/series/yields
  - `geopolitics` context/status/watchlist/evidence/osint-feed/pizza-index/polymarket
  - `polymarket` overview/context
  - `events` recent/history/receipts read views
  - `cross-asset` context
  - additional `alerts` list/history/show/security-status read views
- Still excludes admin/operator and mutation surfaces from the public client.

## 0.1.6

- Added customer-safe read wrappers for order-flow surfaces:
  - `orderflow summary`
  - `orderflow context`
  - `orderflow raw`
  - `orderflow historical`
  - `orderflow liquidity-metrics`
- Added chart artifact rendering wrappers:
  - `chart fx`
  - `chart stocks`
- Updated README and CLI reference with order-flow/chart commands and real redacted output examples.

## 0.1.5

- Rewrote customer-facing README with full client command coverage, setup guidance, Core API alignment notes, response-contract semantics, and real redacted output examples.
- Added `docs/CLI_REFERENCE.md` as a compact customer/operator command reference.
- Documented FX/currency-pair support and clarified when raw pair data is healthy but optional context enrichment may be empty.

## 0.1.4

- Added explicit `fx` CLI group for currency-pair data:
  - `fx quote`
  - `fx bars`
  - `fx indicators`
  - `fx session`
- Clarified README examples for currency-pair access alongside `context fx`.

## 0.1.3

- Added authenticated CLI wrappers for new Core API alignment surfaces:
  - `evidence feed` for live-backed evidence feed reads
  - `alerts metrics`, `alerts recent`, and `alerts dead-letter` for cleaned alert tail checks
  - `context fx`, `context gold`, and `context stocks` for market context smoke/E2E checks
- Synced package version metadata with the hosted Core API upgrade line
- Added tests for the new CLI route mappings and package version guard

## 0.1.2

- Cut hosted-defaults release on PyPI
- Kept default portal/API URLs pointed at hosted managed service endpoints

## 0.1.1

- Synced package docs to current managed Cornerstones product truth after first publication
- Clarified that bounded `guide` / `changelog` discovery flows track server-owned truth surfaces, including signed trial-backed discovery access and the latest cross-asset correlation-evidence additions
- Kept the client package thin instead of adding premature package-side wrappers for upstream product reads that already flow through discovery/changelog endpoints

## 0.1.0

- Initial pre-release package layout for the public-safe Cornerstones client CLI
- Added local config storage for portal URL, API URL, API key, trial cookie, and trial token
- Added anonymous trial start, trial status, and discovery-token commands
- Added public-safe `guide`, `changelog`, and authenticated `verify` flows
- Added packaging metadata and smoke-verification workflow for build/install checks
- Added GitHub Actions CI and publish workflow scaffolding for repo-local verification and future TestPyPI/PyPI release automation
