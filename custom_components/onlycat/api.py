"""OnlyCat API Client."""

from __future__ import annotations
from types import CoroutineType

import socketio
from typing import Any

import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
import logging

from .data import OnlyCatData
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

ONLYCAT_URL = "https://gateway.onlycat.com"

type OnlyCatConfigEntry = ConfigEntry[OnlyCatApiClient]

class OnlyCatApiClientError(Exception):
    """Exception to indicate a general API error."""


class OnlyCatApiClientCommunicationError(
    OnlyCatApiClientError,
):
    """Exception to indicate a communication error."""


class OnlyCatApiClientAuthenticationError(
    OnlyCatApiClientError,
):
    """Exception to indicate an authentication error."""


class OnlyCatApiClient:
    """Only Cat API Client."""

    def __init__(
        self,
        token: str,
        session: aiohttp.ClientSession,
        data: OnlyCatData | None = None,
        socket: socketio.AsyncClient | None = None,
    ) -> None:
        """Sample API Client."""
        self._token = token
        self._data = data
        self._session = aiohttp.ClientSession(connector=ProxyConnector("10.4.0.5",8080,ProxyType.HTTP))
        self._socket = socket or socketio.AsyncClient(
            http_session=self._session,
            reconnection=True,
            reconnection_attempts=10,
            reconnection_delay=10,
            reconnection_delay_max=10,
            logger=True, ssl_verify=False
        )
        self._socket.on("connect", self.on_connect)
        self._socket.on("disconnect", self.on_disconnect)
        self._socket.on("userUpdate", self.on_user_update)
        self._socket.on("*", self.on_any_event)

    async def connect(self) -> None:
        """Connect to the API."""
        if self._socket.connected:
            return
        _LOGGER.debug("Connecting to API")
        
        await self._socket.connect(
            ONLYCAT_URL,
            transports=["websocket"],
            namespaces="/",
            headers={
                "platform": "home-assistant",
                "device": "onlycat-hass"
            },
            auth={
                "token": self._token
            }
        )
        return
    
    async def disconnect(self) -> None:
        """Disconnect from the API."""
        _LOGGER.debug("Disconnecting from API")
        await self._socket.disconnect()
    
    async def on_connect(self) -> None:
        """Handle socket connection."""
        _LOGGER.debug("Connected to API")
    
    async def on_disconnect(self) -> None:
        """Handle socket disconnection."""
        _LOGGER.debug("Disconnected from API")

    async def on_user_update(self, data: dict) -> None:
        """Handle user update event."""
        _LOGGER.debug("User update event received: %s", data)

    def add_event_listener(self, event: str, callback: Any) -> None:
        """Add an event listener."""
        self._socket.on(event, callback)
        _LOGGER.debug("Added event listener for event: %s", event)

    async def send_message(self, event: str, data: any) -> Any | None:
        """Send a message to the API."""
        _LOGGER.debug("Sending message to API: %s", data)
        return await self._socket.call(event, data)

    async def on_any_event(self, event: str, *args: Any) -> None:
        """Handle any event."""
        _LOGGER.debug("Received event: %s with args: %s", event, args)

    async def wait(self) -> None:
        await self._socket.wait()