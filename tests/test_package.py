"""Basic tests for the installed linkeval package."""

import linkeval


def test_package_version() -> None:
    """The package exposes the expected development version."""
    assert linkeval.__version__ == "0.0.1"
