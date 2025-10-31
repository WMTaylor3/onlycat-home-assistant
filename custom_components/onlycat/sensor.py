"""Sensor platform for OnlyCat (one sensor per door policy)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .data.policy import DeviceTransitPolicy

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatApiClient
    from .data import Device, OnlyCatConfigEntry

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="OnlyCat",
    name="Door Policy",
    device_class=None,
    entity_category=EntityCategory.DIAGNOSTIC,
    translation_key="onlycat_policy_configuration_sensor",
)

# # TODO: We are now making this call twice, once in the select.py and once here.
# # Here we only grab the IDs, but we are still making the secondary API calls.
# # Woth moving into the runtime data methinks?
# async def load_policy_ids(api_client: OnlyCatApiClient, device_id: str) -> list[str]:
#     """Fetch only the policy IDs for a device"""
#     resp = await api_client.send_message("getDeviceTransitPolicies", {"deviceId": device_id})
#     if not resp:
#         return []
#     ids: list[str] = []
#     for item in resp:
#         pid = item.get("deviceTransitPolicyId")
#         if pid is None:
#             continue
#         ids.append(str(pid))
#     return ids


# async def load_policies(
#     api_client: OnlyCatApiClient, device_id: str
# ) -> list[dict]:
#     """Load full policy payloads for a device."""
#     policy_ids = await load_policy_ids(api_client, device_id)
#     if not policy_ids:
#         return []

#     # Fetch full policy details in parallel
#     coros = [
#         api_client.send_message("getDeviceTransitPolicy", {"deviceTransitPolicyId": pid})
#         for pid in policy_ids
#     ]
#     responses = await asyncio.gather(*coros, return_exceptions=True)

#     # Filter out errors and return only successful dict responses
#     policies: list[dict] = []
#     for pid, res in zip(policy_ids, responses):
#         if isinstance(res, Exception):
#             _LOGGER.warning(
#                 "Failed to load policy %s for device %s: %s", pid, device_id, res
#             )
#             continue
#         policies.append(res)

#     return policies

async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OnlyCat policy sensors: one sensor per policy returned by the OnlyCat API."""
    entities = []
    for device in entry.runtime_data.devices:
        policies = device.device_transit_policies
        for policy in policies:
            entities.append(
                OnlyCatTransitPolicyConfigSensor(
                    device=device,
                    policy=policy,
                    device_transit_policy_id=policy.device_transit_policy_id,
                    entity_description=ENTITY_DESCRIPTION,
                    api_client=entry.runtime_data.client,
                )
            )
    async_add_entities(entities)

class OnlyCatTransitPolicyConfigSensor(SensorEntity):
    """Sensor representing the configuration of a transit policy."""

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
        policy: DeviceTransitPolicy,
        device_transit_policy_id: int,
        entity_description: SensorEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._state = policy.to_dict()
        self._api_client = api_client
        self._attr_unique_id = (
            f"{device.device_id.replace('-', '_').lower()}_policy_config_{device_transit_policy_id}"
        )
        self.entity_id = "sensor." + self._attr_unique_id
        self.device: Device = device
        self.policy_id = device_transit_policy_id
        # TODO: When we hear back from OnlyCat about whether there is a policyUpdate event, we can change this to use it instead.
        # api_client.add_event_listener("policyUpdate", self.on_policy_update)