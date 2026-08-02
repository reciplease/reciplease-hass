"""Config flow for Reciplease."""

from __future__ import annotations

import logging
from typing import override

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from reciplease_hass import InvalidAuth, ReciplaseClient, ReciplaseConnectionError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class ReciplaseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Sets up a config flow for Reciplease."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ReciplaseClient(
                async_get_clientsession(self.hass),
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
            )
            try:
                house = await client.async_get_self()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ReciplaseConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(house.house_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=house.house_name or "Reciplease",
                    data={
                        CONF_URL: user_input[CONF_URL],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
