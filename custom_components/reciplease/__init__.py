"""The Reciplease integration."""

from __future__ import annotations

from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from reciplease_hass import InvalidAuth, ReciplaseClient, ReciplaseConnectionError

from .coordinator import ReciplaseConfigEntry, ReciplaseCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ReciplaseConfigEntry) -> bool:
    """Set up Reciplease from a config entry."""
    client = ReciplaseClient(
        aiohttp_client.async_get_clientsession(hass),
        entry.data[CONF_URL],
        entry.data[CONF_API_KEY],
    )
    try:
        house = await client.async_get_self()
    except InvalidAuth as err:
        raise ConfigEntryAuthFailed("The Reciplease API key was rejected") from err
    except ReciplaseConnectionError as err:
        raise ConfigEntryNotReady("Could not reach the Reciplease API") from err

    coordinator = ReciplaseCoordinator(hass, entry, client, house)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ReciplaseConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
