"""Tests for Reciplease config entry setup."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reciplease.const import DOMAIN
from reciplease_hass import (
    HouseSelf,
    InvalidAuth,
    PantrySummary,
    PlannedMealsSummary,
    ReciplaseConnectionError,
)

ENTRY_DATA = {
    CONF_URL: "https://reciplease.example.com",
    CONF_API_KEY: "rcpl_testkey1234567890",
}


def _mock_entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, unique_id="house-1", data=ENTRY_DATA)


async def test_setup_entry_success(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with patch("custom_components.reciplease.ReciplaseClient") as mock_client_cls:
        client = mock_client_cls.return_value
        client.async_get_self = AsyncMock(
            return_value=HouseSelf(house_id="house-1", house_name="Test House", role="READ_ONLY")
        )
        client.async_get_pantry_summary = AsyncMock(
            return_value=PantrySummary(total_items=5, expired_items=1)
        )
        client.async_get_planned_meals_summary = AsyncMock(
            return_value=PlannedMealsSummary(upcoming_count=2, next_meal=None)
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.reciplease_test_house_pantry_items").state == "5"


async def test_setup_entry_raises_auth_failed(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with patch("custom_components.reciplease.ReciplaseClient") as mock_client_cls:
        client = mock_client_cls.return_value
        client.async_get_self = AsyncMock(side_effect=InvalidAuth)

        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_entry_not_ready_on_connection_error(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with patch("custom_components.reciplease.ReciplaseClient") as mock_client_cls:
        client = mock_client_cls.return_value
        client.async_get_self = AsyncMock(side_effect=ReciplaseConnectionError)

        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
