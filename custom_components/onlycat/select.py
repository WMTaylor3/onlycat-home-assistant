"""Sensor platform for OnlyCat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .data.device import DeviceUpdate
from .data.policy import DeviceTransitPolicy

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatApiClient
    from .data import Device, OnlyCatConfigEntry

ENTITY_DESCRIPTION = SelectEntityDescription(
    key="OnlyCat",
    name="Door Policy",
    entity_category=EntityCategory.CONFIG,
    icon="mdi:home-clock",
    translation_key="onlycat_policy_select",
)


async def load_policies(
    api_client: OnlyCatApiClient, device_id: str
) -> list[DeviceTransitPolicy]:
    """Load policies for a device."""
    return [
        DeviceTransitPolicy.from_api_response(policy)
        for policy in await api_client.send_message(
            "getDeviceTransitPolicies", {"deviceId": device_id}
        )
    ]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entities = []
    for device in entry.runtime_data.devices:
        policies = await load_policies(entry.runtime_data.client, device.device_id)
        entities.append(
            OnlyCatPolicySelect(
                device=device,
                policies=policies,
                entity_description=ENTITY_DESCRIPTION,
                api_client=entry.runtime_data.client,
            )
        )
    async_add_entities(entities)


class OnlyCatPolicySelect(SelectEntity):
    """Door policy for the flap."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_category = EntityCategory.CONFIG
    _attr_translation_key = "onlycat_policy_select"

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
        policies: list[DeviceTransitPolicy],
        entity_description: SelectEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._state = None
        self._attr_raw_data = None
        self._api_client = api_client
        self._attr_unique_id = device.device_id.replace("-", "_").lower() + "_policy"
        self.entity_id = "select." + self._attr_unique_id
        self._attr_options = [policy.name for policy in policies]
        self.device: Device = device
        self._policies = policies
        if device.device_transit_policy_id is not None:
            self.set_current_policy(device.device_transit_policy_id)
        api_client.add_event_listener("deviceUpdate", self.on_device_update)

    def set_current_policy(self, policy_id: int) -> None:
        """Set the current policy."""
        _LOGGER.debug(
            "Setting policy %s for device %s", policy_id, self.device.device_id
        )

        self._attr_current_option = next(
            p.name for p in self._policies if p.device_transit_policy_id == policy_id
        )

    async def on_device_update(self, data: dict) -> None:
        """Handle device update event."""
        if data["deviceId"] != self.device.device_id:
            return

        _LOGGER.debug("Device update event received for select: %s", data)

        device_update = DeviceUpdate.from_api_response(data)
        if device_update.body.device_transit_policy_id:
            # Reload policies in case a new policy got added in the meantime
            self._policies = await load_policies(
                self._api_client, self.device.device_id
            )
            self._attr_options = [policy.name for policy in self._policies]
            self.set_current_policy(device_update.body.device_transit_policy_id)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Activate a device policy."""
        _LOGGER.debug("Setting policy %s for device %s", option, self.device.device_id)
        policy_id = next(
            p.device_transit_policy_id for p in self._policies if p.name == option
        )
        await self._api_client.send_message(
            "activateDeviceTransitPolicy",
            {"deviceId": self.device.device_id, "deviceTransitPolicyId": policy_id},
        )
