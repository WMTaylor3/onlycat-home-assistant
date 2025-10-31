"""Sensor platform for OnlyCat (one sensor per door policy)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.onlycat.data.device import DeviceUpdate

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatApiClient
    from .data import OnlyCatConfigEntry
    from .data.device import Device
    from .data.policy import DeviceTransitPolicy

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="OnlyCat",
    name="Door Policy",
    device_class=None,
    entity_category=EntityCategory.DIAGNOSTIC,
    translation_key="onlycat_door_policy_configuration_sensor",
)

# TODO: We are now making this call twice, once in the select.py and once here.
# Here we only grab the IDs, but we are still making the secondary API calls.
# Woth moving into the runtime data methinks?
async def load_policy_ids(api_client: OnlyCatApiClient, device_id: str) -> list[str]:
    """Fetch only the policy IDs for a device"""
    resp = await api_client.send_message("getDeviceTransitPolicies", {"deviceId": device_id})
    if not resp:
        return []
    ids: list[str] = []
    for item in resp:
        pid = item.get("deviceTransitPolicyId")
        if pid is None:
            continue
        ids.append(str(pid))
    return ids


async def load_policies(
    api_client: OnlyCatApiClient, device_id: str
) -> list[dict]:
    """Load full policy payloads for a device."""
    policy_ids = await load_policy_ids(api_client, device_id)
    if not policy_ids:
        return []

    # Fetch full policy details in parallel
    coros = [
        api_client.send_message("getDeviceTransitPolicy", {"deviceTransitPolicyId": pid})
        for pid in policy_ids
    ]
    responses = await asyncio.gather(*coros, return_exceptions=True)

    # Filter out errors and return only successful dict responses
    policies: list[dict] = []
    for pid, res in zip(policy_ids, responses):
        if isinstance(res, Exception):
            _LOGGER.warning(
                "Failed to load policy %s for device %s: %s", pid, device_id, res
            )
            continue
        policies.append(res)

    return policies

async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OnlyCat policy sensors: one sensor per policy returned by the OnlyCat API."""
    entities = []
    for device in entry.runtime_data.devices:
        policies = await load_policies(entry.runtime_data.client, device.device_id)
        for policy in policies:
            entities.append(
                OnlyCatDoorPolicyConfigSensor(
                    device=device,
                    policy=policy,
                    policy_id=policy_id,
                    api_client=api_client,
                    entity_description=ENTITY_DESCRIPTION,
                )
            )
    async_add_entities(entities)

class OnlyCatDoorPolicyConfigSensor(SensorEntity):
    """Sensor representing the configuration of a door policy."""

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
        policy: dict,
        policy_id: str,
        entity_description: SensorEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._state = None
        self._attr_raw_data = json.dumps(policy)
        self._api_client = api_client
        self._attr_unique_id = (
            f"{device.device_id.replace('-', '_').lower()}_policy_config_{policy_id}"
        )
        self.entity_id = "sensor." + self._attr_unique_id
        self.device: Device = device
        self.policy_id = policy_id
        api_client.add_event_listener("policyUpdate", self.on_policy_update)

    async def on_policy_update(self, data: dict) -> None:
        # """Handle device update event."""
        # if data["deviceId"] != self.device.device_id:
        #     return

        # device_update = DeviceUpdate.from_api_response(data)
        # if device_update.body.device_transit_policy_id:
        #     # Reload policies in case a new policy got added in the meantime
        #     self._policies = await load_policies(
        #         self._api_client, self.device.device_id
        #     )
        #     self._attr_options = [policy.name for policy in self._policies]
        #     self.set_current_policy(device_update.body.device_transit_policy_id)
        # self.async_write_ha_state()