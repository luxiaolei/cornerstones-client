from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cornerstones_client.release_readiness import evaluate_release_readiness  # noqa: E402


PACKAGE_URLS = {
    "pypi": "https://pypi.org/pypi/cornerstones-client/json",
    "testpypi": "https://test.pypi.org/pypi/cornerstones-client/json",
}


def run(command: list[str], *, cwd: Path = ROOT) -> tuple[bool, str]:
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return False, str(exc)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output


def fetch_status(url: str) -> int | None:
    try:
        with urlopen(url, timeout=20) as response:
            return response.status
    except HTTPError as exc:
        return exc.code
    except URLError:
        return None


def main() -> int:
    python = sys.executable
    local_checks: dict[str, bool] = {}
    command_outputs: dict[str, str] = {}

    local_checks["pytest"], command_outputs["pytest"] = run([python, "-m", "pytest", "-q"])
    run(["rm", "-rf", "build", "dist", "src/cornerstones_client.egg-info"])
    local_checks["build"], command_outputs["build"] = run([python, "-m", "build"])
    local_checks["twine_check"], command_outputs["twine_check"] = run([python, "-m", "twine", "check", "dist/*"])

    smoke_ok = False
    smoke_output = "build failed; smoke install skipped"
    if local_checks["build"]:
        wheel_paths = sorted((ROOT / "dist").glob("*.whl"))
        if wheel_paths:
            venv_dir = Path(tempfile.mkdtemp(prefix="cornerstones-client-release-", dir="/tmp"))
            try:
                created, created_out = run(["/usr/bin/python3", "-m", "venv", str(venv_dir)])
                installed, install_out = run([str(venv_dir / "bin" / "pip"), "install", str(wheel_paths[-1])]) if created else (False, created_out)
                helped, help_out = run([str(venv_dir / "bin" / "cornerstones-client"), "--help"]) if installed else (False, install_out)
                smoke_ok = created and installed and helped
                smoke_output = "\n\n".join(part for part in [created_out, install_out, help_out] if part)
            finally:
                shutil.rmtree(venv_dir, ignore_errors=True)
        else:
            smoke_output = "no wheel found in dist/"
    local_checks["smoke_install"] = smoke_ok
    command_outputs["smoke_install"] = smoke_output

    secrets_ok, secrets_output = run(["gh", "secret", "list", "-R", "luxiaolei/cornerstones-client"])
    command_outputs["gh_secret_list"] = secrets_output
    github_secrets = [line.split()[0] for line in secrets_output.splitlines() if line.strip()] if secrets_ok else []

    package_indices = {name: fetch_status(url) for name, url in PACKAGE_URLS.items()}
    report = evaluate_release_readiness(
        local_checks=local_checks,
        package_indices=package_indices,
        github_secrets=github_secrets,
        github_secrets_known=secrets_ok,
    )
    report["command_outputs"] = command_outputs
    report["package_urls"] = PACKAGE_URLS
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
