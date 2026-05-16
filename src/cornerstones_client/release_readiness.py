from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

REQUIRED_PUBLISH_SECRETS = ("TEST_PYPI_API_TOKEN", "PYPI_API_TOKEN")


def _as_bool_map(values: Mapping[str, Any]) -> dict[str, bool]:
    return {key: bool(value) for key, value in values.items()}


def evaluate_release_readiness(
    *,
    local_checks: Mapping[str, Any],
    package_indices: Mapping[str, int | None | Mapping[str, Any]],
    github_secrets: Iterable[str] | None,
    github_secrets_known: bool = True,
    local_version: str | None = None,
) -> dict[str, Any]:
    normalized_checks = _as_bool_map(local_checks)
    failed_local_checks = [name for name, passed in normalized_checks.items() if not passed]
    local_release_prep_passed = not failed_local_checks

    present_secrets = sorted(set(github_secrets or []))
    missing_secrets = [name for name in REQUIRED_PUBLISH_SECRETS if name not in present_secrets]

    normalized_indices = {
        name: _normalize_index_record(package_indices.get(name), local_version)
        for name in ("pypi", "testpypi")
    }
    published_targets = [
        name
        for name, index in normalized_indices.items()
        if index["status"] == 200 and (local_version is None or index["version_matches_local"])
    ]

    publication_state = {
        "published_targets": published_targets,
        "testpypi_ready": local_release_prep_passed and "TEST_PYPI_API_TOKEN" in present_secrets,
        "pypi_ready": local_release_prep_passed and "PYPI_API_TOKEN" in present_secrets,
    }

    blockers: list[str] = []
    warnings: list[str] = []

    if failed_local_checks:
        blockers.append(f"Local release-prep checks failing: {', '.join(failed_local_checks)}.")

    if local_version is not None:
        for name, index in normalized_indices.items():
            if index["status"] != 200 or index["version_matches_local"]:
                continue
            blockers.append(
                f"{name} published version mismatch: local {local_version}, "
                f"index info.version {index['info_version'] or 'unknown'}, "
                f"has local release {index['has_local_version']}."
            )

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
    passed = passed and not blockers

    return {
        "local_checks": normalized_checks,
        "local_release_prep_passed": local_release_prep_passed,
        "local_version": local_version,
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


def _normalize_index_record(value: Any, local_version: str | None) -> dict[str, Any]:
    if isinstance(value, Mapping):
        status = value.get("status")
        info_version = value.get("info_version")
        releases = _as_sequence(value.get("releases"))
        has_local_version = bool(value.get("has_local_version"))
        if local_version is not None and releases:
            has_local_version = has_local_version or local_version in releases
        latest_release = value.get("latest_release")
        error = value.get("error")
    else:
        status = value
        info_version = None
        releases = []
        has_local_version = False
        latest_release = None
        error = None

    if local_version is None:
        version_matches_local = status == 200
    else:
        version_matches_local = status == 200 and info_version == local_version and has_local_version

    return {
        "status": status,
        "info_version": info_version,
        "latest_release": latest_release,
        "has_local_version": has_local_version,
        "version_matches_local": version_matches_local,
        "error": error,
    }


def _as_sequence(value: Any) -> Sequence[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return value
    return []
