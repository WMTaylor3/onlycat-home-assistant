"""Provides device actions for OnlyCat."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_TYPE,
)
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant

ACTION_UNLOCK = "unlock"
ACTION_TYPES = {ACTION_UNLOCK}
ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): vol.In(ACTION_TYPES)}
)
DEVICE_ACTIONS = [
    {CONF_TYPE: ACTION_UNLOCK, CONF_DOMAIN: DOMAIN},
]
SERVICE_UNLOCK = DOMAIN + ".remote_unlock"


async def async_get_actions(device_id: str) -> list[dict[str, str]]:
    """List device actions for OnlyCat devices."""
    actions = DEVICE_ACTIONS
    for action in actions:
        action[CONF_DEVICE_ID] = device_id
    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, context: Context | None
) -> None:
    """Execute a device action."""
    service_data = {"device_id": config[CONF_DEVICE_ID]}
    service = ""
    if config[CONF_TYPE] == ACTION_UNLOCK:
        service = SERVICE_UNLOCK
    await hass.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )
