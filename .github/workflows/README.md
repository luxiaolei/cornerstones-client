# GitHub Actions notes

## CI
- `ci.yml` runs tests, builds source/wheel distributions, checks metadata with Twine, and smoke-installs the built wheel.
- local preflight mirror: `python scripts/verify_release_readiness.py`

## Publish
- `publish.yml` publishes to TestPyPI or PyPI through repo secrets.
- Required secrets:
  - `TEST_PYPI_API_TOKEN`
  - `PYPI_API_TOKEN`
- Manual trigger:
  - Actions -> Publish Package -> Run workflow -> choose `testpypi` or `pypi`
- Release trigger:
  - publishing to real PyPI also runs automatically when a GitHub Release is published.
- Human-side first-publication runbook:
  - `docs/release/first-publication-runbook.md`
