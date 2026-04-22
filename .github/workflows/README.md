# GitHub Actions notes

## CI
- `ci.yml` runs tests, builds source/wheel distributions, checks metadata with Twine, and smoke-installs the built wheel.
- local preflight mirror: `python scripts/verify_release_readiness.py`

## Publish
- `publish.yml` is prepared but requires repo secrets before it can publish.
- Required secrets:
  - `TEST_PYPI_API_TOKEN`
  - `PYPI_API_TOKEN`
- Manual trigger:
  - Actions -> Publish Package -> Run workflow -> choose `testpypi` or `pypi`
- Release trigger:
  - publishing to real PyPI also runs automatically when a GitHub Release is published.
