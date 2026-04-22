# Changelog

All notable changes to `cornerstones-client` will be documented in this file.

## Unreleased

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
