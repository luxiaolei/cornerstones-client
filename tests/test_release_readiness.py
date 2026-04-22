from cornerstones_client.release_readiness import evaluate_release_readiness


def test_evaluate_release_readiness_flags_missing_publish_path_even_when_local_checks_pass():
    report = evaluate_release_readiness(
        local_checks={
            "pytest": True,
            "build": True,
            "twine_check": True,
            "smoke_install": True,
        },
        package_indices={
            "pypi": 404,
            "testpypi": 404,
        },
        github_secrets=[],
    )

    assert report["local_release_prep_passed"] is True
    assert report["publication_state"]["testpypi_ready"] is False
    assert report["publication_state"]["pypi_ready"] is False
    assert report["passed"] is False
    assert "GitHub repo missing required publish secrets: TEST_PYPI_API_TOKEN, PYPI_API_TOKEN." in report["blockers"]
    assert "Package not yet live on PyPI or TestPyPI." in report["blockers"]


def test_evaluate_release_readiness_passes_when_local_checks_are_green_and_testpypi_publish_path_exists():
    report = evaluate_release_readiness(
        local_checks={
            "pytest": True,
            "build": True,
            "twine_check": True,
            "smoke_install": True,
        },
        package_indices={
            "pypi": 404,
            "testpypi": 404,
        },
        github_secrets=["TEST_PYPI_API_TOKEN"],
    )

    assert report["publication_state"]["testpypi_ready"] is True
    assert report["publication_state"]["pypi_ready"] is False
    assert report["passed"] is True
    assert "Package not yet live on PyPI or TestPyPI." in report["warnings"]


def test_evaluate_release_readiness_fails_when_local_release_prep_checks_are_red():
    report = evaluate_release_readiness(
        local_checks={
            "pytest": True,
            "build": False,
            "twine_check": True,
            "smoke_install": False,
        },
        package_indices={
            "pypi": 404,
            "testpypi": 404,
        },
        github_secrets=["TEST_PYPI_API_TOKEN", "PYPI_API_TOKEN"],
    )

    assert report["local_release_prep_passed"] is False
    assert report["passed"] is False
    assert "Local release-prep checks failing: build, smoke_install." in report["blockers"]


def test_evaluate_release_readiness_does_not_invent_missing_secrets_when_secret_inventory_is_unknown():
    report = evaluate_release_readiness(
        local_checks={
            "pytest": True,
            "build": True,
            "twine_check": True,
            "smoke_install": True,
        },
        package_indices={
            "pypi": 404,
            "testpypi": 404,
        },
        github_secrets=[],
        github_secrets_known=False,
    )

    assert report["passed"] is False
    assert "GitHub publish-secret presence could not be verified." in report["blockers"]
    assert "GitHub repo missing required publish secrets: TEST_PYPI_API_TOKEN, PYPI_API_TOKEN." not in report["blockers"]
