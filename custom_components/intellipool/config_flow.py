"""Config flow for IntelliPool integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IntelliPoolApi, IntelliPoolApiError, IntelliPoolAuthError
from .const import (
    CONF_API_KEY,
    CONF_INSTALLATION_ID,
    CONF_PASSWORD,
    CONF_SESSION_TOKEN,
    CONF_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = voluptuous.Schema(
    {
        voluptuous.Required(CONF_USERNAME): str,
        voluptuous.Required(CONF_PASSWORD): str,
        voluptuous.Optional(CONF_NAME, default="Pool"): str,
    }
)


class IntelliPoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IntelliPool."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._auth_info: dict[str, Any] = {}
        self._installations: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            name = user_input.get(CONF_NAME, "Pool")

            session = async_get_clientsession(self.hass)
            api = IntelliPoolApi(session=session)

            try:
                await api.authenticate(username, password)
                
                # Fetch installations
                installations = await api.get_installations()
                
                if not installations:
                    errors["base"] = "no_data"
                elif len(installations) == 1:
                    # Only one installation, proceed directly
                    install = installations[0]
                    install_id = str(install["installId"])
                    
                    await self.async_set_unique_id(install_id)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_INSTALLATION_ID: install_id,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_NAME: name,
                            # We store the latest known token, but it will be refreshed on startup
                            CONF_SESSION_TOKEN: api.session_token,
                            CONF_API_KEY: api._api_key, # Or constant
                        },
                    )
                else:
                    # Multiple installations, ask user to pick
                    self._auth_info = {
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_NAME: name,
                        CONF_SESSION_TOKEN: api.session_token,
                        CONF_API_KEY: api._api_key,
                    }
                    self._installations = installations
                    return await self.async_step_pick_install()

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

    async def async_step_pick_install(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the installation selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            install_id = user_input[CONF_INSTALLATION_ID]
            
            await self.async_set_unique_id(install_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=self._auth_info[CONF_NAME],
                data={
                    CONF_INSTALLATION_ID: install_id,
                    **self._auth_info
                },
            )

        # Generate options for selection
        options = {
            str(install["installId"]): f"{install.get('name', install['installId'])} ({install['installId']})"
            for install in self._installations
        }

        return self.async_show_form(
            step_id="pick_install",
            data_schema=voluptuous.Schema(
                {voluptuous.Required(CONF_INSTALLATION_ID): voluptuous.In(options)}
            ),
            errors=errors,
        )
