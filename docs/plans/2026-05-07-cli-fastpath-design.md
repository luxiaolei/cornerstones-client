# Cornerstones CLI Fast-Path Design

Date: 2026-05-07
Owner: Zeta / Theta orchestration
Source handoff: `/home/trader/.openclaw/workspace-agents/zeta-home/handoffs/2026-05-07_cornerstones_cli_fastpath_design_handoff.md`

## Goal

Make high-frequency read-only `cornerstones ...` CLI calls materially faster without changing downstream FX OpenClaw source code.

The CLI remains the platform contract. Downstream consumers should keep invoking `cornerstones`, not bypass the CLI with direct API calls.

## Recommendation

Use **Option C architecture, delivered first as an Option A slice**:

1. `cornerstones-client` owns the thin HTTP client behavior: route mapping, auth/config loading adapters, HTTP request, JSON/error formatting.
2. Core `cornerstones` keeps the command name and full admin/runtime surface.
3. Core adds a tiny early entrypoint shim that tries the thin fast-path for supported read-only commands before importing the current heavy CLI.
4. Unsupported, ambiguous, admin/operator, mutation, or fallback-worthy failures use the old core CLI unchanged.

Short form:

```text
cornerstones executable
  -> tiny core entry shim
      -> if supported read-only command and fast-path enabled:
             use client-owned thin HTTP fast-path
         else:
             import old cornerstones.cli.main and run current behavior
```

Do **not** solve this primarily by changing FX downstream invocations. Do **not** make `cornerstones-client` alias shadow all of `cornerstones` on the live machine as the first move.

## Why this design

Current installed command is the core CLI:

```toml
# /home/trader/.openclaw/workspace-main/cornerstones/pyproject.toml
[project.scripts]
cornerstones = "cornerstones.cli.main:main"
```

The slowness is paid before command dispatch. Console scripts import `cornerstones.cli.main` before calling `main()`, and that module currently imports heavy runtime/domain chains at module import time.

Observed import/startup shape:

- `cornerstones.cli.main` import median: about `2.7s`.
- `cornerstones_client.cli` import median: about `0.3s`.
- `cornerstones health status` median: about `2.8s` even though `/health` direct API median was about `7ms`.
- `cornerstones cross-asset context` median: about `4.3s`; direct API median about `1.0s`.
- `cornerstones context fx --symbol EURUSD` median: about `4.4s`; direct API median about `1.6s`.

Main import culprit:

```text
cornerstones.cli.main
  -> cornerstones.domains.alerts.e2e_harness
  -> cornerstones.domains.__init__
  -> fx/stocks/gold/orderflow/cross_asset/options/alerts/geopolitics routes/services
  -> FastAPI/auth/provider/service modules
```

Even if a `maybe_fastpath(argv)` is added inside the current `main()`, the old console wrapper has already imported `cornerstones.cli.main`, so most startup cost is already lost. Therefore speed-max path needs either:

- a new light entrypoint module, plus regenerated console script; or
- a severe lazy-import refactor of `cornerstones.cli.main` so importing it is cheap.

Best first implementation uses the new light entrypoint. Also lazy-move the worst top-level import in old `main.py` as cleanup.

## Repo ownership

### `cornerstones-client` owns

Create a small reusable fast-path package under client:

```text
/home/trader/.openclaw/workspace-main/cornerstones-client/src/cornerstones_client/fastpath/
  __init__.py
  config.py       # client/core credential profiles, base URL, redaction-safe auth
  routes.py       # argv -> RequestSpec table
  http.py         # minimal GET helper, JSON/error formatting
  runner.py       # try_run(argv, profile, prog) -> handled/unsupported/exit_code
```

Responsibilities:

- table-driven supported command parsing;
- route + query parameter mapping;
- auth header construction without printing secrets;
- config profile support for both:
  - public client config: `~/.config/cornerstones-client/config.json`;
  - core CLI credentials/config: `~/.config/cornerstones/credentials.json` and related core defaults;
- raw JSON-compatible output formatting;
- clear unsupported/fallback signal.

### Core `cornerstones` owns

Core keeps the `cornerstones` command and all slow/full local/admin functionality.

Add:

```text
/home/trader/.openclaw/workspace-main/cornerstones/src/cornerstones/cli/entry.py
/home/trader/.openclaw/workspace-main/cornerstones/src/cornerstones/cli/fastpath_bridge.py  # optional adapter if not importing client directly
```

Change script entry after implementation:

```toml
[project.scripts]
cornerstones = "cornerstones.cli.entry:main"
```

Entrypoint shape:

```python
def main(argv=None):
    import os
    import sys

    argv = sys.argv[1:] if argv is None else list(argv)

    if os.getenv("CORNERSTONES_CLI_FASTPATH", "1") != "0":
        try:
            from cornerstones_client.fastpath.runner import try_run
            result = try_run(argv, profile="core", prog="cornerstones")
            if result.handled:
                raise SystemExit(result.exit_code)
        except Exception:
            # Never let fast-path break full CLI availability.
            # Optional debug env can log class name only, no secrets.
            pass

    from cornerstones.cli.main import main as slow_main
    slow_main()
```

Important rollout note: changing `pyproject.toml` alone does not update an existing console script. Deployment must regenerate/reinstall the entrypoint, or directly replace the live shim in a controlled release step.

## First fast-path command slice

Start with read-only commands used by FX/agent loops. Keep output schema as close as possible to current core CLI success output.

| Existing CLI shape | Method + route | Params | Notes |
|---|---:|---|---|
| `cornerstones health status` | `GET /health` | none | no auth; fastest sanity path |
| `cornerstones context fx --symbol EURUSD` | `GET /v1/context/fx` | `symbol`, optional `timeframe`, `count` | preserve JSON body |
| `cornerstones fx quote --symbol EURUSD` | `GET /v1/fx/quote` | `symbol` | downstream uses this too |
| `cornerstones fx bars --symbol EURUSD --timeframe M15` | `GET /v1/fx/bars` | `symbol`, `timeframe`, optional `count`/`bars` | normalize only if server requires; otherwise preserve accepted values |
| `cornerstones fx indicators --symbol EURUSD --timeframe M15` | `GET /v1/fx/indicators` | `symbol`, `timeframe`, optional `bars` | high-frequency |
| `cornerstones fx session --symbol EURUSD` | `GET /v1/fx/session` | `symbol`, optional `timeframe`, `bars` | downstream observed |
| `cornerstones cross-asset context` | `GET /v1/cross-asset/context` | none | client currently uses bare `cross-asset`; fast parser must accept core shape |
| `cornerstones stocks quote --symbol GLD` | `GET /v1/stocks/quote` | `symbol` | high-frequency GLD/proxy use |
| `cornerstones stocks context --symbol GLD --bars-count 3` | `GET /v1/stocks/context` | `symbol`, `bars_count` | preserve `bars-count` flag |
| `cornerstones context gold` | `GET /v1/gold/context` | optional params | likely next after first green |

Do not fast-path in first slice:

- `auth` mutations;
- admin/operator commands;
- migrations/local DB inspection;
- alert dispatch/replay/resolve/test;
- subscriptions unless explicitly scoped;
- chart rendering until output/artifact semantics are reviewed;
- orderflow admin surfaces;
- anything requiring local runtime internals or local fallback to be authoritative.

## Downstream compatibility findings

Downstream uses `cornerstones`, not `cornerstones-client`. No downstream `cornerstones-client` literal found.

Observed runtime/test command families include:

```text
cornerstones context fx --symbol <symbol>
cornerstones fx quote --symbol <symbol>
cornerstones fx bars --symbol <symbol> --timeframe <tf>
cornerstones fx indicators --symbol <symbol> --timeframe <tf>
cornerstones fx session --symbol <symbol>
cornerstones cross-asset context
cornerstones stocks quote --symbol GLD
cornerstones stocks context --symbol GLD
cornerstones macro summary
cornerstones macro yields
cornerstones orderflow raw|summary|context|historical|liquidity-metrics --symbol <symbol>
cornerstones events export --format fx-event-detector
cornerstones context gold
cornerstones geopolitics context
cornerstones polymarket context
```

Some downstream code already emits shapes current core CLI rejects, for example:

```text
cornerstones cross-asset context --symbol <symbol>
cornerstones macro summary --symbol <symbol>
cornerstones macro yields --symbol <symbol>
```

Decision for first implementation:

- For compatibility-safe commands, preserve old failure behavior unless there is clear downstream value in accepting ignored optional `--symbol`.
- For `cross-asset context --symbol`, consider accepting and ignoring `--symbol` in fast path if the route is symbol-agnostic and downstream is already attempting it. Add tests documenting this as a compatibility repair, not a semantic change.

## Error and fallback semantics

Fast path must be fail-open to the old CLI unless it is certain it fully handled the command.

Return modes:

```text
unsupported argv -> handled=False -> import old CLI
parse ambiguous / unknown flags -> handled=False -> old argparse behavior
HTTP success -> print raw JSON -> handled=True exit 0
missing auth for data route -> handled=True with current-style not_logged_in/auth error JSON, or fallback if exact parity uncertain
HTTP 401/403 from server -> handled=True, do not local-fallback-hide real auth failure
HTTP 404/405/501 -> handled=False -> old CLI may have local implementation/fallback
connection refused / timeout -> handled=False by default for first slice, so old CLI fallback can run
CORNERSTONES_CLI_FASTPATH=0 -> handled=False always
```

Optional debug:

```text
CORNERSTONES_CLI_FASTPATH_DEBUG=1
```

If enabled, print only non-secret labels to stderr, e.g. `fastpath unsupported`, `fastpath fallback http_404`, `fastpath exception TimeoutError`. Never print key, token, URL with embedded credentials, DB URL, or config values.

## Performance targets

Benchmark SLOs for local warm service:

| Command | Current rough median | Target after first slice |
|---|---:|---:|
| `cornerstones health status` | ~2.8s | `<0.5s` |
| `cornerstones fx indicators ...` | ~2.9s | direct API latency + `<0.3-0.5s` |
| `cornerstones cross-asset context` | ~4.3s | direct API latency + `<0.3-0.5s` |
| `cornerstones context fx ...` | ~4.4s | direct API latency + `<0.3-0.5s` |

Hard requirement:

- Supported fast-path commands must not import `cornerstones.domains.*`, FastAPI routes, provider adapters, Playwright, IB/Rithmic, chart services, or alerts E2E harness.

## Benchmark harness

Add a repeatable script in core or shared tooling:

```text
/home/trader/.openclaw/workspace-main/cornerstones/scripts/benchmark_cli_fastpath.py
```

Required behavior:

- runs direct API and CLI commands for N iterations;
- suppresses response JSON by default;
- never prints credentials;
- reports median, p90, min, max, and calculated CLI overhead over direct API;
- supports `--json` output for regression artifacts.

Example manual baseline:

```bash
cd /home/trader/.openclaw/workspace-main/cornerstones
python -X importtime -m cornerstones.cli.main --help 2> /tmp/cornerstones-core-importtime.txt || true
/usr/bin/time -f 'elapsed=%e' cornerstones health status >/tmp/cornerstones-health-status.json
/usr/bin/time -f 'elapsed=%e' cornerstones context fx --symbol EURUSD >/tmp/cornerstones-context-fx.json
/usr/bin/time -f 'elapsed=%e' cornerstones fx indicators --symbol EURUSD --timeframe M15 >/tmp/cornerstones-fx-indicators.json
/usr/bin/time -f 'elapsed=%e' cornerstones cross-asset context >/tmp/cornerstones-cross-asset.json
```

Direct API comparison must load saved credentials locally but never print them.

## Tests

### Client repo tests

Likely files:

```text
cornerstones-client/tests/test_fastpath_routes.py
cornerstones-client/tests/test_fastpath_runner.py
cornerstones-client/tests/test_fastpath_config.py
```

Coverage:

- argv maps to route + params for first slice;
- `cross-asset context` and bare client-style `cross-asset` both supported where intended;
- core profile reads core credential shape without printing values;
- client profile still uses public client config;
- mocked HTTP success prints raw JSON payload, not a wrapper;
- 401/403 are surfaced, not hidden by fallback;
- 404/connection errors return fallback signal when configured;
- no secret appears in stderr/stdout on failures.

Run:

```bash
cd /home/trader/.openclaw/workspace-main/cornerstones-client
PYTHONPATH=src pytest -q
```

### Core repo tests

Likely files:

```text
cornerstones/tests/test_cli_fastpath_entry.py
cornerstones/tests/test_cli_fastpath_no_heavy_import.py
cornerstones/tests/test_cli_fastpath_fallback.py
```

Coverage:

- `entry.main([supported...])` calls client fastpath and never imports `cornerstones.cli.main` on success;
- `CORNERSTONES_CLI_FASTPATH=0` imports old CLI path;
- unsupported/admin commands import old CLI path;
- fastpath exception falls back to old CLI;
- `sys.modules` after fast-path success does not contain heavy modules:
  - `cornerstones.domains.alerts.e2e_harness`
  - `cornerstones.domains.charting.service`
  - `cornerstones.providers.ib.adapter`
  - `ib_insync`
  - `playwright`
  - route modules if avoidable;
- current JSON formatting parity for representative mocked responses.

Run focused slices first:

```bash
cd /home/trader/.openclaw/workspace-main/cornerstones
PYTHONPATH=src pytest -q tests/test_cli_fastpath_entry.py tests/test_cli_fastpath_no_heavy_import.py tests/test_cli_fastpath_fallback.py
```

Then run adjacent CLI tests if time budget allows:

```bash
PYTHONPATH=src pytest -q tests/test_cli.py
```

If full `tests/test_cli.py` hangs or exceeds time, report focused green separately and capture the blocker honestly.

## Implementation phases

### Phase 0 — design and baseline

- Keep repos read-only except this design doc.
- Record baseline timings and importtime artifacts.
- Confirm live service healthy.

### Phase 1 — client-owned fastpath module

- Add `cornerstones_client.fastpath` package.
- Add tests for route mapping, config profiles, output, and fallback decision semantics.
- Keep `cornerstones-client` public CLI behavior unchanged initially, or refactor only after tests guard route parity.

### Phase 2 — core entry shim

- Add `cornerstones.cli.entry`.
- Add core tests proving supported commands avoid old `cornerstones.cli.main` import.
- Update `pyproject.toml` script entrypoint.
- Move `AlertsE2EHarness` import in `cornerstones.cli.main` into the exact alerts E2E handler as cleanup.
- Consider lazy-loading `httpx`/dotenv only if fastpath still imports old `main.py` somewhere; entry shim should avoid this already.

### Phase 3 — local canary

- Regenerate console script via editable reinstall or controlled wrapper update.
- Verify `command -v cornerstones` points to expected script.
- Verify `cornerstones health status` uses fast path and meets target.
- Verify supported data commands.
- Verify unsupported/admin command still goes through old CLI.

### Phase 4 — FX no-code-change smoke

Run with trading disabled:

```bash
cd /home/trader/.openclaw/workspace-agents/fx-openclaw-trading
FX_EXECUTE_TRADES=0 OPENCLAW_SCHEDULED_SYMBOL=EURUSD OPENCLAW_SCHEDULED_HORIZON=15m \
  timeout 180s ./agents/fx-trading-data/agent/main.py
```

Confirm logs show faster Cornerstones acquisition and no broker/order/risk/fund changes.

### Phase 5 — broaden command coverage

After first slice is stable, add more read-only customer surfaces:

- `macro summary`, `macro yields`;
- `orderflow raw|summary|context|historical|liquidity-metrics` read-only paths;
- `events export --format fx-event-detector` if output contract can match;
- `geopolitics context`, `polymarket context`;
- chart paths only after artifact/output semantics and browser-render timeouts are reviewed.

## Rollback

Fast rollback layers:

1. Set environment:

```bash
CORNERSTONES_CLI_FASTPATH=0
```

2. Revert core entrypoint commit or regenerate old console script:

```toml
cornerstones = "cornerstones.cli.main:main"
```

3. If client fastpath package has a bug but core fallback works, leave client package installed and disable fast path.

Never change downstream FX source as rollback unless a separate downstream bug is proven.

## Security notes

- Do not print API keys, bearer tokens, trial tokens, cookies, DB URLs, connection strings, or raw credential files.
- Benchmark scripts must suppress response bodies by default.
- Debug output may include labels and HTTP status only.
- Auth errors from server must not be hidden by local fallback when saved credentials exist.

## Acceptance criteria

Design acceptance:

- `cornerstones` command preserved.
- No downstream FX source changes required.
- Client/core ownership split explicit.
- First command set and route mapping explicit.
- Import-chain root cause identified.
- Benchmark harness and SLOs defined.
- Test plan includes mapping, output, no-heavy-import, fallback, env gate, and auth-error behavior.
- Rollout/rollback safe.

Implementation acceptance:

- Supported commands avoid heavy imports.
- `cornerstones health status` drops from ~2.8s to `<0.5s` locally.
- Data commands become direct API latency + `<0.3-0.5s` overhead.
- Output JSON contract remains compatible for success cases.
- Unsupported/admin/local commands still work through old CLI.
- `CORNERSTONES_CLI_FASTPATH=0` restores old behavior.
- Core and client focused tests pass.
- Live no-code-change FX smoke passes with `FX_EXECUTE_TRADES=0`.
