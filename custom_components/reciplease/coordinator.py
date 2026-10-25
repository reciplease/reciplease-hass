"""DataUpdateCoordinator for the Reciplease integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from reciplease_hass import (
    HouseSelf,
    PantrySummary,
    PlannedMealsSummary,
    ReciplaseClient,
    ReciplaseConnectionError,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=30)


@dataclass
class ReciplaseData:
    """Data fetched on each coordinator refresh."""

    pantry: PantrySummary
    planned_meals: PlannedMealsSummary


type ReciplaseConfigEntry = ConfigEntry[ReciplaseCoordinator]


class ReciplaseCoordinator(DataUpdateCoordinator[ReciplaseData]):
    """Polls the Reciplease API for house-scoped data."""

    config_entry: ReciplaseConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ReciplaseConfigEntry,
        client: ReciplaseClient,
        house: HouseSelf,
    ) -> None:
        """Set up the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Reciplease",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.house = house

    async def _async_update_data(self) -> ReciplaseData:
        try:
            pantry = await self.client.async_get_pantry_summary()
            planned_meals = await self.client.async_get_planned_meals_summary()
        except ReciplaseConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return ReciplaseData(pantry=pantry, planned_meals=planned_meals)
