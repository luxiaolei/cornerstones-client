# Cornerstones Client

Public-safe CLI for the managed Cornerstones product.

## What it does

`cornerstones-client` gives downstream operators and agents a compact local client for:

- storing the managed product portal URL and API URL separately
- storing an issued product API key locally
- starting a limited anonymous browser-compatible trial against the hosted portal
- minting and caching a short-lived discovery trial token
- reading public-safe discovery surfaces such as `guide` and `changelog`
- verifying a real authenticated API key against `/v1/status`

## Current command surface

```bash
cornerstones-client auth set-base-url --base-url https://your-cornerstones-portal
cornerstones-client auth set-api-base-url --api-base-url https://your-cornerstones-api
cornerstones-client trial start
cornerstones-client trial token
cornerstones-client guide
cornerstones-client changelog
cornerstones-client auth login --api-key <issued-api-key>
cornerstones-client verify
cornerstones-client auth status
```

## Install

Public PyPI publication is being prepared but is not live yet.

Until the first public release, install from a checked-out source tree or from a locally built wheel:

```bash
python -m pip install .
```

For machine-checkable local release readiness on a packaging host:

```bash
python scripts/verify_release_readiness.py
```

That preflight verifies:

- `pytest -q`
- local `build` + `twine check`
- clean-venv wheel smoke install
- current PyPI/TestPyPI package presence
- current GitHub publish-secret presence

For local packaging verification by hand:

```bash
python -m build
python -m pip install dist/cornerstones_client-0.1.0-py3-none-any.whl
cornerstones-client --help
```

## Trial and auth notes

- `guide` and `changelog` automatically request a short-lived discovery token if no full API key is present yet.
- `verify` is intentionally stricter and requires a real issued API key.
- Trial and discovery surfaces are limited-scope onboarding helpers, not a claim that every authenticated surface is available anonymously.

## Config

The client stores local state in the user config directory as `cornerstones-client/config.json`.

Stored fields currently include:

- `portal_base_url`
- `api_base_url`
- `api_key`
- `trial_cookie`
- `trial_token`

## Status

This package is a pre-release public-safe client surface under active productization.
Current focus is packaging hardening, truthful onboarding, stable discovery flows, and release automation.

## Repository automation

This repo now includes GitHub Actions workflows for:

- CI verification on push and pull request
- package build + metadata checks
- smoke install of built wheel
- manual or release-driven publish workflow once PyPI/TestPyPI tokens are configured
