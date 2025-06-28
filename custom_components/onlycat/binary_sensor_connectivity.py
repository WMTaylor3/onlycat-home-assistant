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
    from . import Device
    from .api import OnlyCatApiClient

ENTITY_DESCRIPTION = BinarySensorEntityDescription(
    key="OnlyCat",
    name="OnlyCat Flap",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
)


class OnlyCatConnectionSensor(BinarySensorEntity):
    """OnlyCat Sensor class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "onlycat_connection_sensor"

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
        self._state = None
        self._attr_raw_data = None
        self.device = device
        self._attr_name = "Connectivity"
        self._attr_unique_id = (
            device.device_id.replace("-", "_").lower() + "_connectivity"
        )
        self.entity_id = "binary_sensor." + self._attr_unique_id
        api_client.add_event_listener("deviceUpdate", self.on_device_update)

    async def on_device_update(self, data: dict) -> None:
        """Handle device update event."""
        if data["deviceId"] != self.device.device_id:
            return

        _LOGGER.debug("Device update event received for connectivity sensor: %s", data)

        self._attr_raw_data = str(data)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return if device is connected."""
        return self.device.connectivity.connected
