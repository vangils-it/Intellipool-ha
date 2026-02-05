"""IntelliPool API client with WebSocket support for control."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Callable

import aiohttp

from .const import API_BASE_URL, API_ENDPOINT, WS_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class IntelliPoolApiError(Exception):
    """Exception for API errors."""


class IntelliPoolAuthError(IntelliPoolApiError):
    """Exception for authentication errors."""


class IntelliPoolApi:
    """IntelliPool API client with REST and WebSocket support."""

    def __init__(
        self,
        installation_id: str,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
        session_token: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._installation_id = installation_id
        self._api_key = api_key
        self._session = session
        self._session_token = session_token
        self._close_session = False
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._ws_connected = False
        self._message_id = 0
        self._pending_responses: dict[int, asyncio.Future] = {}
        self._listeners: list[Callable[[dict], None]] = []
        self._access_levels: dict[str, str] = {}

    @property
    def installation_id(self) -> str:
        """Return the installation ID."""
        return self._installation_id

    @property
    def session_token(self) -> str | None:
        """Return the session token."""
        return self._session_token

    @session_token.setter
    def session_token(self, value: str) -> None:
        """Set the session token."""
        self._session_token = value

    @property
    def access_levels(self) -> dict[str, str]:
        """Return the access levels for values."""
        return self._access_levels

    def can_write(self, key: str) -> bool:
        """Check if a value can be written."""
        return self._access_levels.get(key) == "WRITE"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True
        return self._session

    async def close(self) -> None:
        """Close the session and WebSocket if we created them."""
        await self.ws_disconnect()
        if self._close_session and self._session:
            await self._session.close()

    # ========== REST API Methods ==========

    async def get_probes(self) -> dict[str, Any]:
        """Get probe data from the REST API."""
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

    # ========== WebSocket Methods ==========

    def _generate_signature(self, timestamp: int) -> str:
        """Generate the signature for WebSocket authentication.
        
        The signature appears to be SHA1(apiKey + sessionToken + timestamp).
        This may need adjustment based on actual implementation.
        """
        if not self._session_token:
            raise IntelliPoolAuthError("Session token required for WebSocket")
        
        # Try different signature generation methods
        # Method 1: SHA1(sessionToken + timestamp)
        data = f"{self._session_token}{timestamp}"
        return hashlib.sha1(data.encode()).hexdigest()

    def _next_message_id(self) -> int:
        """Get the next message ID."""
        self._message_id += 1
        return self._message_id

    async def ws_connect(self) -> bool:
        """Connect to the WebSocket and authenticate."""
        if self._ws_connected:
            return True

        if not self._session_token:
            raise IntelliPoolAuthError("Session token required for WebSocket connection")

        session = await self._get_session()
        
        try:
            ws_url = f"{WS_ENDPOINT}"
            _LOGGER.debug("Connecting to WebSocket: %s", ws_url)
            
            self._ws = await session.ws_connect(
                ws_url,
                headers={
                    "Origin": "file://",
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15",
                },
            )
            
            # Send authentication message
            timestamp = int(time.time() * 1000)
            signature = self._generate_signature(timestamp)
            
            auth_msg = {
                "id": self._next_message_id(),
                "apiKey": "intellipool-webapp",
                "sessionToken": self._session_token,
                "timestamp": timestamp,
                "signature": signature,
                "data": {
                    "type": "CHECK_SESSION",
                    "appVersion": "1.4.0"
                }
            }
            
            await self._ws.send_json(auth_msg)
            _LOGGER.debug("Sent auth message: %s", auth_msg)
            
            # Start listening for messages
            self._ws_connected = True
            asyncio.create_task(self._ws_listener())
            
            # Wait for access levels response
            await asyncio.sleep(1)
            
            return True
            
        except aiohttp.ClientError as err:
            _LOGGER.error("WebSocket connection failed: %s", err)
            self._ws_connected = False
            return False

    async def ws_disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._ws_connected = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _ws_listener(self) -> None:
        """Listen for WebSocket messages."""
        if not self._ws:
            return
            
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_ws_message(data)
                    except json.JSONDecodeError:
                        _LOGGER.warning("Invalid JSON from WebSocket: %s", msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error("WebSocket error: %s", self._ws.exception())
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.info("WebSocket closed")
                    break
        except Exception as err:
            _LOGGER.error("WebSocket listener error: %s", err)
        finally:
            self._ws_connected = False

    async def _handle_ws_message(self, data: dict) -> None:
        """Handle incoming WebSocket message."""
        msg_type = data.get("type")
        
        _LOGGER.debug("Received WebSocket message: %s", data)
        
        if msg_type == "VALUES_ACCESS_LEVEL":
            # Store access levels
            self._access_levels = data.get("data", {})
            _LOGGER.info("Received access levels for %d values", len(self._access_levels))
            
        elif msg_type == "SUCCESS":
            # Handle response to our request
            msg_id = data.get("id")
            if msg_id in self._pending_responses:
                self._pending_responses[msg_id].set_result(data)
                
        elif msg_type == "ERROR":
            msg_id = data.get("id")
            if msg_id in self._pending_responses:
                self._pending_responses[msg_id].set_exception(
                    IntelliPoolApiError(f"WebSocket error: {data}")
                )
        
        # Notify listeners
        for listener in self._listeners:
            try:
                listener(data)
            except Exception as err:
                _LOGGER.error("Listener error: %s", err)

    async def ws_send_command(self, command_type: str, data: dict | None = None) -> dict:
        """Send a command via WebSocket and wait for response."""
        if not self._ws_connected or not self._ws:
            await self.ws_connect()
        
        if not self._ws:
            raise IntelliPoolApiError("WebSocket not connected")
        
        msg_id = self._next_message_id()
        timestamp = int(time.time() * 1000)
        signature = self._generate_signature(timestamp)
        
        message = {
            "id": msg_id,
            "apiKey": "intellipool-webapp",
            "sessionToken": self._session_token,
            "timestamp": timestamp,
            "signature": signature,
            "data": {
                "type": command_type,
                **(data or {})
            }
        }
        
        # Create a future for the response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_responses[msg_id] = future
        
        try:
            await self._ws.send_json(message)
            _LOGGER.debug("Sent command: %s", message)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=10.0)
            return response
            
        except asyncio.TimeoutError:
            raise IntelliPoolApiError("Command timeout")
        finally:
            self._pending_responses.pop(msg_id, None)

    async def set_value(self, key: str, value: Any) -> bool:
        """Set a value via WebSocket.
        
        Args:
            key: The value key (e.g., 'OMEOTECH_FLAG_LIGHTING')
            value: The value to set
            
        Returns:
            True if successful
        """
        if not self.can_write(key):
            raise IntelliPoolApiError(f"Value {key} is not writable")
        
        # The exact command format needs to be determined from more captures
        # This is a placeholder based on typical patterns
        response = await self.ws_send_command(
            "SET_VALUE",
            {
                "key": key,
                "value": value,
                "installationId": self._installation_id,
            }
        )
        
        return response.get("type") == "SUCCESS"

    async def set_lighting(self, state: bool) -> bool:
        """Turn lighting on or off."""
        return await self.set_value("OMEOTECH_FLAG_LIGHTING", str(state).lower())

    async def set_lighting_color(self, color: str) -> bool:
        """Set lighting color."""
        return await self.set_value("LIGHTING_COLOR", color)

    async def set_aux1(self, state: bool) -> bool:
        """Turn auxiliary 1 on or off."""
        return await self.set_value("OMEOTECH_FLAG_AUX1", str(state).lower())

    def add_listener(self, callback: Callable[[dict], None]) -> Callable[[], None]:
        """Add a listener for WebSocket messages.
        
        Returns a function to remove the listener.
        """
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback)
