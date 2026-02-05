"""The IntelliPool integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IntelliPoolApi
from .const import CONF_API_KEY, CONF_INSTALLATION_ID, CONF_SESSION_TOKEN, DOMAIN
from .coordinator import IntelliPoolDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Base platforms (always loaded)
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Control platforms (loaded only if session_token is provided)
CONTROL_PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IntelliPool from a config entry."""
    installation_id = entry.data[CONF_INSTALLATION_ID]
    api_key = entry.data[CONF_API_KEY]
    session_token = entry.data.get(CONF_SESSION_TOKEN)

    session = async_get_clientsession(hass)
    api = IntelliPoolApi(installation_id, api_key, session, session_token)

    coordinator = IntelliPoolDataUpdateCoordinator(hass, api, installation_id)
    await coordinator.async_config_entry_first_refresh()

    # If we have a session token, try to connect WebSocket for control
    if session_token:
        try:
            connected = await api.ws_connect()
            if connected:
                _LOGGER.info("WebSocket connected - control features enabled")
            else:
                _LOGGER.warning("WebSocket connection failed - control features disabled")
        except Exception as err:
            _LOGGER.warning("WebSocket connection error: %s - control features disabled", err)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Determine which platforms to load
    platforms_to_load = list(PLATFORMS)
    if session_token and api.access_levels:
        platforms_to_load.extend(CONTROL_PLATFORMS)
        _LOGGER.info("Loading control platforms (switches)")

    await hass.config_entries.async_forward_entry_setups(entry, platforms_to_load)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Determine which platforms were loaded
    session_token = entry.data.get(CONF_SESSION_TOKEN)
    platforms_to_unload = list(PLATFORMS)
    if session_token:
        platforms_to_unload.extend(CONTROL_PLATFORMS)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, platforms_to_unload):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Close WebSocket connection
        await coordinator.api.close()

    return unload_ok
