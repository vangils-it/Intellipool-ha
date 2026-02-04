"""Binary sensor platform for IntelliPool integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BINARY_SENSOR_TYPES, DOMAIN
from .coordinator import IntelliPoolDataUpdateCoordinator
from .entity import IntelliPoolEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IntelliPool binary sensors based on a config entry."""
    coordinator: IntelliPoolDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[IntelliPoolBinarySensor] = []

    # Create binary sensors for each available type in the data
    for type_info, sensor_config in BINARY_SENSOR_TYPES.items():
        if type_info in coordinator.data:
            entities.append(
                IntelliPoolBinarySensor(
                    coordinator=coordinator,
                    type_info=type_info,
                    name=sensor_config["name"],
                    device_class=sensor_config["device_class"],
                    icon=sensor_config["icon"],
                )
            )

    async_add_entities(entities)


class IntelliPoolBinarySensor(IntelliPoolEntity, BinarySensorEntity):
    """Representation of an IntelliPool binary sensor."""

    def __init__(
        self,
        coordinator: IntelliPoolDataUpdateCoordinator,
        type_info: str,
        name: str,
        device_class: str,
        icon: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, type_info, name)
        
        # Map device class strings to BinarySensorDeviceClass
        device_class_map = {
            "running": BinarySensorDeviceClass.RUNNING,
            "heat": BinarySensorDeviceClass.HEAT,
            "light": BinarySensorDeviceClass.LIGHT,
        }
        if device_class in device_class_map:
            self._attr_device_class = device_class_map[device_class]
        
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self._type_info not in self.coordinator.data:
            return None

        value = self.coordinator.data[self._type_info].get("value")
        
        if value is None:
            return None

        # Handle string boolean values
        if isinstance(value, str):
            return value.lower() == "true"
        
        return bool(value)
