"""Sensors for the Reciplease integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ReciplaseConfigEntry, ReciplaseData
from .entity import ReciplaseEntity


@dataclass(frozen=True, kw_only=True)
class ReciplaseSensorEntityDescription(SensorEntityDescription):
    """Describes a Reciplease sensor and how to read its value from coordinator data."""

    value_fn: Callable[[ReciplaseData], StateType]


type StateType = str | int | None

SENSOR_DESCRIPTIONS: tuple[ReciplaseSensorEntityDescription, ...] = (
    ReciplaseSensorEntityDescription(
        key="inventory_items",
        translation_key="inventory_items",
        native_unit_of_measurement="items",
        state_class="measurement",
        value_fn=lambda data: data.inventory.total_items,
    ),
    ReciplaseSensorEntityDescription(
        key="expired_inventory_items",
        translation_key="expired_inventory_items",
        native_unit_of_measurement="items",
        state_class="measurement",
        value_fn=lambda data: data.inventory.expired_items,
    ),
    ReciplaseSensorEntityDescription(
        key="upcoming_planned_meals",
        translation_key="upcoming_planned_meals",
        native_unit_of_measurement="meals",
        state_class="measurement",
        value_fn=lambda data: data.planned_meals.upcoming_count,
    ),
    ReciplaseSensorEntityDescription(
        key="next_planned_meal",
        translation_key="next_planned_meal",
        value_fn=lambda data: (
            data.planned_meals.next_meal.name if data.planned_meals.next_meal else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReciplaseConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Reciplease sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        ReciplaseSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class ReciplaseSensor(ReciplaseEntity, SensorEntity):
    """A Reciplease sensor backed by an EntityDescription value function."""

    entity_description: ReciplaseSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the sensor's current value."""
        return self.entity_description.value_fn(self.coordinator.data)
