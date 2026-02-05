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

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IntelliPool from a config entry."""
    installation_id = entry.data[CONF_INSTALLATION_ID]
    api_key = entry.data[CONF_API_KEY]
    session_token = entry.data.get(CONF_SESSION_TOKEN)

    session = async_get_clientsession(hass)
    api = IntelliPoolApi(
        installation_id, 
        api_key, 
        session,
        session_token=session_token,
    )

    # If we have a session token, try to connect WebSocket for control
    if session_token:
        try:
            await api.ws_connect()
            _LOGGER.info("WebSocket connected - control features enabled")
        except Exception as err:
            _LOGGER.warning("WebSocket connection failed, control features disabled: %s", err)

    coordinator = IntelliPoolDataUpdateCoordinator(hass, api, installation_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

    return unload_ok
