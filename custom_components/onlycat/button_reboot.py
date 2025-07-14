"""Unlcok Button for OnlyCat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .api import OnlyCatApiClient
    from .data.device import Device

ENTITY_DESCRIPTION = ButtonEntityDescription(
    key="OnlyCat",
    name="Reboot",
    device_class=ButtonDeviceClass.RESTART,
    translation_key="onlycat_reboot_button",
)


class OnlyCatRebootButton(ButtonEntity):
    """OnlyCat reboot button class."""

    _attr_has_entity_name = True
    _attr_should_poll = False

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
        """Initialize the button class."""
        self.entity_description = ENTITY_DESCRIPTION
        self.device: Device = device
        self._attr_unique_id = device.device_id.replace("-", "_").lower() + "_reboot"
        self._api_client = api_client
        self.entity_id = "button." + self._attr_unique_id

    async def async_press(self) -> None:
        """Handle button press."""
        await self._api_client.send_message(
            "runDeviceCommand", {"deviceId": self.device.device_id, "command": "reboot"}
        )
