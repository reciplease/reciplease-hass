"""Base entity for the Reciplease integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReciplaseCoordinator


class ReciplaseEntity(CoordinatorEntity[ReciplaseCoordinator], Entity):
    """Defines a Reciplease entity."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ReciplaseCoordinator, description: EntityDescription
    ) -> None:
        """Initialize the entity and declare unique id based on description key."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.house.house_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.house.house_id)},
            name=coordinator.house.house_name or "Reciplease",
            manufacturer="Reciplease",
        )
