"""Sensor platform for IntelliPool integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import IntelliPoolDataUpdateCoordinator
from .entity import IntelliPoolEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IntelliPool sensors based on a config entry."""
    coordinator: IntelliPoolDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[IntelliPoolSensor] = []

    # Create sensors for each available type in the data
    for type_info, sensor_config in SENSOR_TYPES.items():
        if type_info in coordinator.data:
            entities.append(
                IntelliPoolSensor(
                    coordinator=coordinator,
                    type_info=type_info,
                    name=sensor_config["name"],
                    device_class=sensor_config["device_class"],
                    native_unit=sensor_config["native_unit"],
                    icon=sensor_config["icon"],
                    state_class=sensor_config.get("state_class"),
                )
            )

    async_add_entities(entities)


class IntelliPoolSensor(IntelliPoolEntity, SensorEntity):
    """Representation of an IntelliPool sensor."""

    def __init__(
        self,
        coordinator: IntelliPoolDataUpdateCoordinator,
        type_info: str,
        name: str,
        device_class: str | None,
        native_unit: str | None,
        icon: str,
        state_class: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, type_info, name)
        
        if device_class:
            self._attr_device_class = SensorDeviceClass(device_class)
        self._attr_native_unit_of_measurement = native_unit
        self._attr_icon = icon
        if state_class:
            self._attr_state_class = SensorStateClass(state_class)

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        if self._type_info not in self.coordinator.data:
            return None

        value = self.coordinator.data[self._type_info].get("value")
        
        if value is None or value == "--.-":
            return None

        # Try to convert to float for numeric sensors
        try:
            # Handle values like "+6.8"
            return float(value)
        except (ValueError, TypeError):
            return value
