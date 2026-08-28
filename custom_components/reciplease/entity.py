"""Base entity for the Reciplease integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

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
        # has_entity_name's default object_id derivation combines area + device name,
        # which produces entity_ids like sensor.kitchen_bayview_gardens_pantry_items
        # once the device is assigned to an area — not obviously tied to this
        # integration at a glance. Set entity_id explicitly instead, so every entity
        # we create is unambiguously ours regardless of area assignment.
        # (suggested_object_id is a read-only property computed from name/has_entity_name
        # — there's no supported attribute to influence it, hence setting entity_id
        # directly. All current subclasses are sensors; revisit the hardcoded domain
        # if a non-sensor platform is ever added.)
        house_slug = slugify(coordinator.house.house_name or coordinator.house.house_id)
        self.entity_id = f"sensor.reciplease_{house_slug}_{description.key}"
