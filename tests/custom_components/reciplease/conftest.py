"""Fixtures for Reciplease integration tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ visible to Home Assistant's component loader."""
    yield
