"""Base entity for IntelliPool integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IntelliPoolDataUpdateCoordinator


class IntelliPoolEntity(CoordinatorEntity[IntelliPoolDataUpdateCoordinator]):
    """Base class for IntelliPool entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IntelliPoolDataUpdateCoordinator,
        type_info: str,
        name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._type_info = type_info
        self._attr_unique_id = f"{coordinator.installation_id}_{type_info}"
        self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.installation_id)},
            name="IntelliPool",
            manufacturer="Pentair",
            model="IntelliPool",
        )
