"""Adds config flow for OnlyCat."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify
import logging

_LOGGER = logging.getLogger(__name__)

from .api import (
    OnlyCatApiClient,
    OnlyCatApiClientAuthenticationError,
    OnlyCatApiClientCommunicationError,
    OnlyCatApiClientError,
)
from .const import DOMAIN, LOGGER


class OnlyCatFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for OnlyCat."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                _LOGGER.debug("Testing credentials and fetching ID")
                client = OnlyCatApiClient(
                    token=user_input[CONF_ACCESS_TOKEN],
                    session=async_create_clientsession(self.hass),
                )
                id = None
                # TODO: Terrible way to do this. Should be synchronous
                async def on_user_update(data):
                    nonlocal id
                    if data is None or "id" not in data:
                        raise OnlyCatApiClientAuthenticationError("ID not found")
                    id = str(data["id"])
                client.add_event_listener("userUpdate", on_user_update)
                await client.connect()
                await client.disconnect()
            except OnlyCatApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except OnlyCatApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except OnlyCatApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                if id is None:
                    id = slugify(user_input[CONF_ACCESS_TOKEN])
                await self.async_set_unique_id(unique_id=id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=id,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ACCESS_TOKEN,
                        default=(user_input or {}).get(CONF_ACCESS_TOKEN, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    )
                },
            ),
            errors=_errors,
        )
