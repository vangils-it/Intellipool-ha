"""Config flow for IntelliPool integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IntelliPoolApi, IntelliPoolApiError, IntelliPoolAuthError
from .const import CONF_API_KEY, CONF_INSTALLATION_ID, CONF_SESSION_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INSTALLATION_ID): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SESSION_TOKEN): str,
        vol.Optional(CONF_NAME, default="Pool"): str,
    }
)


class IntelliPoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IntelliPool."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            installation_id = user_input[CONF_INSTALLATION_ID]
            api_key = user_input[CONF_API_KEY]
            name = user_input.get(CONF_NAME, "Pool")

            # Check if already configured
            await self.async_set_unique_id(installation_id)
            self._abort_if_unique_id_configured()

            # Test the connection
            session = async_get_clientsession(self.hass)
            api = IntelliPoolApi(installation_id, api_key, session)

            try:
                data = await api.get_probes()
                if not data:
                    errors["base"] = "no_data"
                else:
                    entry_data = {
                        CONF_INSTALLATION_ID: installation_id,
                        CONF_API_KEY: api_key,
                        CONF_NAME: name,
                    }
                    # Add session token if provided (enables control features)
                    session_token = user_input.get(CONF_SESSION_TOKEN)
                    if session_token:
                        entry_data[CONF_SESSION_TOKEN] = session_token
                    
                    return self.async_create_entry(
                        title=name,
                        data=entry_data,
                    )
            except IntelliPoolAuthError:
                errors["base"] = "invalid_auth"
            except IntelliPoolApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
