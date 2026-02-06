"""Switch platform for IntelliPool integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH_TYPES
from .coordinator import IntelliPoolDataUpdateCoordinator
from .entity import IntelliPoolEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IntelliPool switches based on a config entry."""
    coordinator: IntelliPoolDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[IntelliPoolSwitch] = []

    # Create switches for each available controllable type
    for type_info, switch_config in SWITCH_TYPES.items():
        if type_info in coordinator.data:
            # Check if we have write access (requires WebSocket connection)
            if coordinator.api.can_write(type_info):
                entities.append(
                    IntelliPoolSwitch(
                        coordinator=coordinator,
                        type_info=type_info,
                        name=switch_config["name"],
                        icon=switch_config["icon"],
                    )
                )
            else:
                _LOGGER.debug(
                    "Skipping switch for %s - no write access", type_info
                )

    async_add_entities(entities)


class IntelliPoolSwitch(IntelliPoolEntity, SwitchEntity):
    """Representation of an IntelliPool switch."""

    def __init__(
        self,
        coordinator: IntelliPoolDataUpdateCoordinator,
        type_info: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, type_info, name)
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self._type_info not in self.coordinator.data:
            return None

        value = self.coordinator.data[self._type_info].get("value")
        
        if value is None:
            return None

        # Handle string boolean values
        if isinstance(value, str):
            return value.lower() == "true"
        
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on %s", self._type_info)
        try:
            await self.coordinator.api.set_value(self._type_info, "true")
            # Request an update
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self._type_info, err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off %s", self._type_info)
        try:
            await self.coordinator.api.set_value(self._type_info, "false")
            # Request an update
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self._type_info, err)
            raise
