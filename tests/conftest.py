"""Shared fixtures for jellyfin_recently_added tests."""
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ visible to Home Assistant for every test."""
    yield
