"""Basic tests for the installed linkeval package."""

from importlib.metadata import version

import linkeval


def test_package_version_matches_distribution_metadata() -> None:
    """The public version matches the installed distribution metadata."""
    assert linkeval.__version__ == version("linkeval")
