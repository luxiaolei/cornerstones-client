from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

REQUIRED_PUBLISH_SECRETS = ("TEST_PYPI_API_TOKEN", "PYPI_API_TOKEN")


def _as_bool_map(values: Mapping[str, Any]) -> dict[str, bool]:
    return {key: bool(value) for key, value in values.items()}


def evaluate_release_readiness(
    *,
    local_checks: Mapping[str, Any],
    package_indices: Mapping[str, int | None],
    github_secrets: Iterable[str] | None,
    github_secrets_known: bool = True,
) -> dict[str, Any]:
    normalized_checks = _as_bool_map(local_checks)
    failed_local_checks = [name for name, passed in normalized_checks.items() if not passed]
    local_release_prep_passed = not failed_local_checks

    present_secrets = sorted(set(github_secrets or []))
    missing_secrets = [name for name in REQUIRED_PUBLISH_SECRETS if name not in present_secrets]

    normalized_indices = {name: package_indices.get(name) for name in ("pypi", "testpypi")}
    published_targets = [name for name, status in normalized_indices.items() if status == 200]

    publication_state = {
        "published_targets": published_targets,
        "testpypi_ready": local_release_prep_passed and "TEST_PYPI_API_TOKEN" in present_secrets,
        "pypi_ready": local_release_prep_passed and "PYPI_API_TOKEN" in present_secrets,
    }

    blockers: list[str] = []
    warnings: list[str] = []

    if failed_local_checks:
        blockers.append(f"Local release-prep checks failing: {', '.join(failed_local_checks)}.")

    if not github_secrets_known and not published_targets:
        blockers.append("GitHub publish-secret presence could not be verified.")
    elif missing_secrets and not published_targets:
        blockers.append(
            f"GitHub repo missing required publish secrets: {', '.join(missing_secrets)}."
        )

    if not published_targets:
        target_message = "Package not yet live on PyPI or TestPyPI."
        if publication_state["testpypi_ready"] or publication_state["pypi_ready"]:
            warnings.append(target_message)
        else:
            blockers.append(target_message)

    passed = local_release_prep_passed and bool(
        published_targets or publication_state["testpypi_ready"] or publication_state["pypi_ready"]
    )

    return {
        "local_checks": normalized_checks,
        "local_release_prep_passed": local_release_prep_passed,
        "github": {
            "secret_inventory_known": github_secrets_known,
            "required_publish_secrets": list(REQUIRED_PUBLISH_SECRETS),
            "present_secrets": present_secrets,
            "missing_publish_secrets": missing_secrets,
        },
        "package_indices": normalized_indices,
        "publication_state": publication_state,
        "passed": passed,
        "blockers": blockers,
        "warnings": warnings,
    }
