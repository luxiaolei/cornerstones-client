# Cornerstones Client — First Publication Runbook

## Current verified truth

As of 2026-04-22 on NY-Ubuntu after first publication:

- local `pytest -q` passes
- local package build passes
- local `twine check dist/*` passes
- clean-venv wheel smoke install passes
- GitHub Actions CI exists and has passed on `main`
- TestPyPI package endpoint is live:
  - `https://test.pypi.org/pypi/cornerstones-client/json` -> `200`
- PyPI package endpoint is live:
  - `https://pypi.org/pypi/cornerstones-client/json` -> `200`
- repo publish secrets are configured:
  - `TEST_PYPI_API_TOKEN`
  - `PYPI_API_TOKEN`

Machine-checkable local preflight:

```bash
cd /home/trader/.openclaw/workspace-main/cornerstones-client
/home/trader/miniconda3/bin/python scripts/verify_release_readiness.py
```

## Recommended release order

1. make TestPyPI publish path live first
2. verify install from TestPyPI in a clean environment
3. then publish real PyPI
4. verify install from real PyPI

## Route A — API token secrets (fastest)

Use this if you want the current `publish.yml` workflow to work without changing workflow auth shape.

### 1. Create package indexes and tokens

On TestPyPI and PyPI:

- create/register project owner access for `cornerstones-client`
- generate API token for TestPyPI
- generate API token for PyPI

Keep token values out of repo and shell history.

### 2. Add GitHub repo secrets

Repo: `luxiaolei/cornerstones-client`

Required secrets:

- `TEST_PYPI_API_TOKEN`
- `PYPI_API_TOKEN`

You can add them in GitHub web UI, or with `gh` locally:

```bash
gh secret set TEST_PYPI_API_TOKEN -R luxiaolei/cornerstones-client
gh secret set PYPI_API_TOKEN -R luxiaolei/cornerstones-client
```

### 3. Trigger TestPyPI publish

Manual workflow path:

- GitHub -> `cornerstones-client` -> Actions -> `Publish Package`
- `Run workflow`
- target: `testpypi`

CLI path:

```bash
gh workflow run publish.yml \
  -R luxiaolei/cornerstones-client \
  -f target=testpypi
```

### 4. Watch workflow result

```bash
gh run list -R luxiaolei/cornerstones-client --workflow publish.yml --limit 5
gh run view -R luxiaolei/cornerstones-client --log-failed <RUN_ID>
```

### 5. Verify TestPyPI live

```bash
python - <<'PY'
import urllib.request, urllib.error
url = 'https://test.pypi.org/pypi/cornerstones-client/json'
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        print(r.status)
except urllib.error.HTTPError as e:
    print(e.code)
PY
```

Expected: `200`

### 6. Verify install from TestPyPI

```bash
/usr/bin/python3 -m venv /tmp/cornerstones-client-testpypi
. /tmp/cornerstones-client-testpypi/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple cornerstones-client
cornerstones-client --help
```

If this passes, move to PyPI.

### 7. Publish real PyPI

Manual workflow path:

- same workflow
- target: `pypi`

CLI path:

```bash
gh workflow run publish.yml \
  -R luxiaolei/cornerstones-client \
  -f target=pypi
```

### 8. Verify real PyPI live

```bash
python - <<'PY'
import urllib.request, urllib.error
url = 'https://pypi.org/pypi/cornerstones-client/json'
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        print(r.status)
except urllib.error.HTTPError as e:
    print(e.code)
PY
```

Expected: `200`

### 9. Verify install from PyPI

```bash
/usr/bin/python3 -m venv /tmp/cornerstones-client-pypi
. /tmp/cornerstones-client-pypi/bin/activate
pip install --upgrade pip
pip install cornerstones-client
cornerstones-client --help
```

## Route B — Trusted publisher (cleaner long-term)

Use this if you want to avoid long-lived API tokens.

### What changes

Current `publish.yml` uses token secrets with:

- `TEST_PYPI_API_TOKEN`
- `PYPI_API_TOKEN`

Trusted publisher would instead require:

1. configure publisher on TestPyPI/PyPI web side
2. bind publisher to GitHub repo/workflow/environment
3. patch `publish.yml` to use OIDC-based publishing instead of password secrets

### Minimum binding facts to record correctly

- owner: `luxiaolei`
- repo: `cornerstones-client`
- workflow file: `publish.yml`
- environments used now:
  - `testpypi`
  - `pypi`

### Recommendation

For fastest first release: use **Route A**.

After first successful publication, consider a follow-up slice that migrates publish auth to trusted publisher.

## Post-release README/install cleanup

After TestPyPI or PyPI is actually live, update these truth surfaces:

- `README.md`
- `.github/workflows/README.md`
- any web/docs install copy pointing at source-only install

Do not update them before live package endpoints return `200`.

## Rollback / failure handling

### If publish workflow fails before upload completes

- inspect failed workflow logs
- fix repo/workflow/metadata issue
- rerun workflow

### If TestPyPI upload succeeds but install is bad

- fix package
- bump version
- republish to TestPyPI

### If real PyPI publish succeeds but package is broken

PyPI artifacts are immutable. Normal recovery shape:

1. fix package
2. bump version
3. publish new version
4. optionally yank bad version in PyPI web UI if needed

Do not overwrite an existing version.

## Fast current blocker check

```bash
cd /home/trader/.openclaw/workspace-main/cornerstones-client
/home/trader/miniconda3/bin/python scripts/verify_release_readiness.py
```

Current expected state on this repo:

- `TEST_PYPI_API_TOKEN` configured
- `PYPI_API_TOKEN` configured
- package live on TestPyPI
- package live on PyPI
- package docs/changelog may still need follow-up sync whenever the managed `cornerstones` service adds new public-safe product truth
