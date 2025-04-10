"""Sensor platform for OnlyCat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatApiClient
    from .data import OnlyCatConfigEntry


ENTITY_DESCRIPTION = BinarySensorEntityDescription(
    key="OnlyCat",
    name="OnlyCat Flap",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    devices = []
    for device in entry.data["devices"]:
        info = await entry.runtime_data.client.send_message(
            "getDevice", {"deviceId": device["deviceId"], "subscribe": True}
        )
        devices.append(device | info)
    async_add_entities(
        OnlyCatConnectionSensor(
            device=device,
            entity_description=ENTITY_DESCRIPTION,
            api_client=entry.runtime_data.client,
        )
        for device in devices
    )


class OnlyCatConnectionSensor(BinarySensorEntity):
    """OnlyCat Sensor class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "OnlyCatDeviceSensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to map to a device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device["deviceId"])},
            name=self.device["description"],
            serial_number=self.device["deviceId"],
        )

    def __init__(
        self,
        device: dict,
        entity_description: BinarySensorEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self._attr_name = None
        self.entity_description = entity_description
        self._state = None
        self._attr_raw_data = None
        self.device = device
        self._attr_unique_id = device["deviceId"] + "_connectivity"
        api_client.add_event_listener("deviceUpdate", self.on_device_update)

    async def on_device_update(self, data: dict) -> None:
        """Handle device update event."""
        _LOGGER.debug("Device update event received: %s", data)
        self._attr_raw_data = str(data)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return if device is connected."""
        return self.device["connectivity"]["connected"]
