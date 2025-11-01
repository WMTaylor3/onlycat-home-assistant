"""Sensor platform for OnlyCat (one sensor per door policy)."""

from __future__ import annotations

import json
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
        ## Home Assistant attributes and state
        self.entity_description = entity_description
        self._attr_native_value = policy.name # JSON payload exceeds the length limit for state values. Used name here. State stored as attribute.
        self._attr_translation_placeholders = {
            "policy_name": policy.name,
        }
        self._attr_unique_id = (
            device.device_id.replace("-", "_").lower()
            + "_policy_config_"
            + str(device_transit_policy_id)
            + "_"
            + policy.name
        )
        self._attr_extra_state_attributes = {
            "policy_name": policy.name,
            "policy_id": device_transit_policy_id,
            "policy_json": json.dumps(policy.to_dict(), indent=2),
            "currently_active": device.device_transit_policy_id == device_transit_policy_id,
        }

        ## Internal helpers
        self.device: Device = device
        self.policy: DeviceTransitPolicy = policy
        self.policy_id = device_transit_policy_id
        self._api_client = api_client

        # TODO: When we hear back from OnlyCat about whether there is a policyUpdate event, we can change this to use it instead.
        # api_client.add_event_listener("policyUpdate", self.on_policy_update)