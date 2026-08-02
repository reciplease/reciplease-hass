"""Tests for the Reciplease config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reciplease.const import DOMAIN
from reciplease_hass import HouseSelf, InvalidAuth, ReciplaseConnectionError

USER_INPUT = {
    CONF_URL: "https://reciplease.example.com",
    CONF_API_KEY: "rcpl_testkey1234567890",
}


async def _start_flow(hass: HomeAssistant) -> dict:
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


@pytest.fixture
def mock_reciplease_client():
    """Patch ReciplaseClient as used by the config flow."""
    with patch("custom_components.reciplease.config_flow.ReciplaseClient") as mock_client_cls:
        client = mock_client_cls.return_value
        client.async_get_self = AsyncMock(
            return_value=HouseSelf(house_id="house-1", house_name="Test House", role="READ_ONLY")
        )
        yield client


async def test_user_flow_creates_an_entry(hass: HomeAssistant, mock_reciplease_client) -> None:
    result = await _start_flow(hass)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test House"
    assert result["data"] == USER_INPUT


async def test_user_flow_aborts_if_the_house_is_already_configured(
    hass: HomeAssistant, mock_reciplease_client
) -> None:
    result = await _start_flow(hass)
    await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    result = await _start_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_shows_invalid_auth(hass: HomeAssistant, mock_reciplease_client) -> None:
    mock_reciplease_client.async_get_self.side_effect = InvalidAuth
    result = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_shows_cannot_connect(hass: HomeAssistant, mock_reciplease_client) -> None:
    mock_reciplease_client.async_get_self.side_effect = ReciplaseConnectionError
    result = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_flow_updates_the_api_key(hass: HomeAssistant, mock_reciplease_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="house-1", data=USER_INPUT)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "rcpl_newkey1234567890"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_KEY] == "rcpl_newkey1234567890"


async def test_reauth_flow_shows_invalid_auth(hass: HomeAssistant, mock_reciplease_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="house-1", data=USER_INPUT)
    entry.add_to_hass(hass)
    mock_reciplease_client.async_get_self.side_effect = InvalidAuth

    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "rcpl_badkey1234567890"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
