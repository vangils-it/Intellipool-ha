"""IntelliPool API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class IntelliPoolApiError(Exception):
    """Exception for API errors."""


class IntelliPoolAuthError(IntelliPoolApiError):
    """Exception for authentication errors."""


class IntelliPoolApi:
    """IntelliPool API client."""

    def __init__(
        self,
        installation_id: str,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._installation_id = installation_id
        self._api_key = api_key
        self._session = session
        self._close_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._close_session and self._session:
            await self._session.close()

    async def get_probes(self) -> dict[str, Any]:
        """Get probe data from the API."""
        session = await self._get_session()
        
        url = f"{API_BASE_URL}{API_ENDPOINT.format(installation_id=self._installation_id)}"
        params = {"key": self._api_key}

        _LOGGER.debug("Fetching data from %s", url)

        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 401:
                    raise IntelliPoolAuthError("Invalid API key")
                if response.status == 403:
                    raise IntelliPoolAuthError("Access forbidden - check API key and installation ID")
                if response.status == 404:
                    raise IntelliPoolApiError("Installation not found - check installation ID")
                if response.status != 200:
                    raise IntelliPoolApiError(f"API error: HTTP {response.status}")

                data = await response.json()
                _LOGGER.debug("Received data: %s", data)
                return self._parse_probes(data)

        except aiohttp.ClientError as err:
            raise IntelliPoolApiError(f"Connection error: {err}") from err

    def _parse_probes(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse probe data into a dictionary keyed by typeInfo."""
        result = {}
        
        values = data.get("values", [])
        for item in values:
            type_info = item.get("typeInfo")
            if type_info:
                result[type_info] = {
                    "value": item.get("value"),
                    "unit": item.get("unit"),
                }
        
        return result

    async def test_connection(self) -> bool:
        """Test the API connection."""
        try:
            await self.get_probes()
            return True
        except IntelliPoolApiError:
            return False
