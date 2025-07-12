"""Provides services for OnlyCat."""

import logging

import voluptuous as vol
from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .device_tracker import OnlyCatPetTracker

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Create services for OnlyCat."""
    hass.services.async_register(
        DOMAIN,
        "set_pet_location",
        async_handle_set_pet_presence,
        schema=vol.Schema(
            {
                vol.Required("device_tracker"): cv.entity_id,
                vol.Required("location"): cv.string,
            }
        ),
    )


async def async_handle_set_pet_presence(call: ServiceCall) -> ServiceResponse:
    """Handle the set presence service call."""
    device_tracker_id: str = call.data["device_tracker"]
    location: str = call.data["location"]

    entity_component = call.hass.data.get("entity_components", {}).get("device_tracker")
    if not entity_component:
        error = "Device tracker component not found"
        raise ServiceValidationError(error)
    entity_obj = entity_component.get_entity(device_tracker_id)
    if not entity_obj:
        error = f"Entity {device_tracker_id} not found"
        raise ServiceValidationError(error)
    if not isinstance(entity_obj, OnlyCatPetTracker):
        error = f"Entity {device_tracker_id} is not an OnlyCatPetTracker entity"
        raise ServiceValidationError(error)
    new_state = STATE_HOME if location.lower() == "home" else STATE_NOT_HOME
    await entity_obj.manual_update_location(new_state)
    _LOGGER.info("Set %s presence to: %s", device_tracker_id, location)
