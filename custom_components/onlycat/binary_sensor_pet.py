"""Sensor platform for OnlyCat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .data.event import Event, EventTriggerSource, EventUpdate
from .data.policy import PolicyResult

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .api import OnlyCatApiClient
    from .data.pet import Pet

ENTITY_DESCRIPTION = BinarySensorEntityDescription(
    key="OnlyCat",
    name="OnlyCat Flap",
    device_class=BinarySensorDeviceClass.PRESENCE,
)


class OnlyCatPetSensor(BinarySensorEntity):
    """OnlyCat Sensor class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_translation_key = "onlycat_pet_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to map to a device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.device_id)},
            name=self.device.description,
            serial_number=self.device.device_id,
        )

    def determine_new_state(self, event: Event) -> None:
        """Determine the new state of the sensor based on the event."""
        if not self.device.device_transit_policy:
            _LOGGER.debug(
                "No transit policy set, unable to determine policy result for event %s",
                event.event_id,
            )
            return
        if event.event_trigger_source not in (
            EventTriggerSource.OUTDOOR_MOTION,
            EventTriggerSource.INDOOR_MOTION,
        ):
            _LOGGER.debug("Event was not triggered by motion, ignoring event.")
            return

        policy_result = self.device.device_transit_policy.determine_policy_result(event)
        if policy_result == PolicyResult.LOCKED:
            _LOGGER.debug(
                "Transit was not allowed, ignoring event for %s.", self.pet_name
            )
        elif policy_result == PolicyResult.UNKNOWN:
            _LOGGER.debug(
                "Unable to determine policy result, ignoring event for %s.",
                self.pet_name,
            )
        elif event.event_trigger_source == EventTriggerSource.OUTDOOR_MOTION:
            _LOGGER.debug(
                "Transit allowed for outdoor motion, assuming %s is present.",
                self.pet_name,
            )
            self._state = True
        else:
            _LOGGER.debug(
                "Transit allowed for indoor motion, assuming %s is not present.",
                self.pet_name,
            )
            self._state = False

    def __init__(
        self,
        pet: Pet,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = ENTITY_DESCRIPTION
        self._attr_raw_data = None
        self.device = pet.device
        self.pet = pet
        self.pet_name = pet.label if pet.label is not None else pet.rfid_code
        self._attr_name = self.pet_name + " Presence"
        self._attr_unique_id = (
            self.device.device_id.replace("-", "_").lower()
            + "_"
            + pet.rfid_code
            + "_presence"
        )
        self._api_client = api_client
        self.entity_id = "sensor." + self._attr_unique_id
        self._state = False
        if pet.last_seen_event:
            self.determine_new_state(pet.last_seen_event)
        api_client.add_event_listener("eventUpdate", self.on_event_update)

    async def on_event_update(self, data: dict) -> None:
        """Handle event update event."""
        if data["deviceId"] != self.device.device_id:
            return

        _LOGGER.debug("Event update event received for pet sensor: %s", data)

        event_update = EventUpdate.from_api_response(data)

        # Wait until frame count is present, i.e., event is finished
        if not event_update.body.frame_count:
            return

        event = Event.from_api_response(
            await self._api_client.send_message(
                "getEvent",
                {
                    "deviceId": self.device.device_id,
                    "eventId": event_update.event_id,
                    "subscribe": False,
                },
            )
        )

        if event.rfid_codes is not None and self.pet.rfid_code in event.rfid_codes:
            _LOGGER.debug("New event for %s, determining new state", self.pet_name)
            self.determine_new_state(event)
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return if device is connected."""
        return self._state
