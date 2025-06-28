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
from .data.event import Event, EventUpdate

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .api import OnlyCatApiClient
    from .data.device import Device

ENTITY_DESCRIPTION = BinarySensorEntityDescription(
    key="OnlyCat",
    name="OnlyCat Flap",
    device_class=BinarySensorDeviceClass.MOTION,
)


class OnlyCatEventSensor(BinarySensorEntity):
    """OnlyCat Sensor class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_translation_key = "onlycat_event_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to map to a device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.device_id)},
            name=self.device.description,
            serial_number=self.device.device_id,
        )

    def __init__(
        self,
        device: Device,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = ENTITY_DESCRIPTION
        self._state = False
        self._attr_raw_data = None
        self.device = device
        self._attr_name = "Flap event"
        self._attr_unique_id = device.device_id.replace("-", "_").lower() + "_event"
        self._api_client = api_client
        self.entity_id = "sensor." + self._attr_unique_id
        api_client.add_event_listener("deviceEventUpdate", self.on_device_event_update)
        api_client.add_event_listener("eventUpdate", self.on_event_update)

    async def on_event_update(self, data: dict) -> None:
        """Handle event update event."""
        if data["deviceId"] != self.device.device_id:
            return

        _LOGGER.debug("Event update event received for event sensor: %s", data)

        event_update = EventUpdate.from_api_response(data)

        if (self._attr_extra_state_attributes["eventId"]) != event_update.event_id:
            _LOGGER.debug("Event ID has changed, updating state.")
            self._state = True
        elif event_update.body:
            if event_update.body.frame_count:
                self._state = False
            if event_update.body.event_classification:
                self._attr_extra_state_attributes["eventClassification"] = (
                    event_update.body.event_classification.name
                )
            if event_update.body.rfid_codes:
                self._attr_extra_state_attributes["rfidCodes"] = (
                    event_update.body.rfid_codes
                )
        self.async_write_ha_state()

    async def on_device_event_update(self, data: dict) -> None:
        """Handle device event update event."""
        if data["deviceId"] != self.device.device_id:
            return

        _LOGGER.debug("Device event update event received for event sensor: %s", data)

        response = await self._api_client.send_message(
            "getEvent",
            {
                "deviceId": data["deviceId"],
                "eventId": data["eventId"],
                "subscribe": True,
            },
        )
        _LOGGER.debug("Response from getEvent: %s", response)
        event = Event.from_api_response(response)

        self._state = True
        self._attr_extra_state_attributes = {
            "eventId": event.event_id,
            "timestamp": event.timestamp,
            "eventTriggerSource": event.event_trigger_source.name,
        }
        if event.event_classification:
            self._attr_extra_state_attributes["eventClassification"] = (
                event.event_classification.name
            )

        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return if device is connected."""
        return self._state
