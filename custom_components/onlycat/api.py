"""OnlyCat API Client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiohttp

    from .data import OnlyCatData

import socketio

_LOGGER = logging.getLogger(__name__)

ONLYCAT_URL = "https://gateway.onlycat.com"


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
        self._session = session
        self._socket = socket or socketio.AsyncClient(
            http_session=self._session,
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=10,
            reconnection_delay_max=10,
            ssl_verify=False,
        )
        self._socket.on("*", self.on_any_event)
        self._socket.on("connect", self.on_connected)


    async def connect(self) -> None:
        """Connect to wesocket client."""
        if self._socket.connected:
            return
        _LOGGER.debug("Connecting to API")
        await self._socket.connect(
            ONLYCAT_URL,
            transports=["websocket"],
            namespaces="/",
            headers={"platform": "home-assistant", "device": "onlycat-hass"},
            auth={"token": self._token},
        )
        return

    async def disconnect(self) -> None:
        """Disconnect websocket client."""
        _LOGGER.debug("Disconnecting from API")
        await self._socket.disconnect()
        await self._socket.shutdown()

    def add_event_listener(self, event: str, callback: Any) -> None:
        """Add an event listener."""
        self._socket.on(event, callback)
        _LOGGER.debug("Added event listener for event: %s", event)

    async def send_message(self, event: str, data: any) -> Any | None:
        """Send a message to the API."""
        _LOGGER.debug("Sending message to API: %s", data)
        return await self._socket.call(event, data)

    async def on_any_event(self, event: str, *args: Any) -> None:
        """Handle any event for debugging."""
        _LOGGER.debug("Received event: %s with args: %s", event, args)

    async def wait(self) -> None:
        """Wait until client is disconnected."""
        await self._socket.wait()

    async def on_connected(self) -> None:
        """Handle connected event."""
        _LOGGER.debug("(Re)connected to API")
