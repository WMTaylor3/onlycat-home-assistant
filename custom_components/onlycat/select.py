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

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatApiClient
    from .data import OnlyCatConfigEntry


ENTITY_DESCRIPTION = SelectEntityDescription(
    key="OnlyCat",
    name="OnlyCat Door Policy",
    icon="mdi:home-clock",
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    policies = []
    entities = []
    for device in entry.data["devices"]:
        policies = await entry.runtime_data.client.send_message(
            "getDeviceTransitPolicies", {"deviceId": device["deviceId"]}
        )
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
    """
    Door policy for the flap.

    Fetched via ["getDeviceTransitPolicies",{"deviceId":"OC-XXXXXXXXXXX"}]
    Example response:
    [[{"deviceTransitPolicyId":0000,"deviceId":"OC-XXXXXXXXXXX","name":"Nachts"},
        {"deviceTransitPolicyId":0000,"deviceId":"OC-XXXXXXXXXXX","name":"Offen"},
        {"deviceTransitPolicyId":0000,"deviceId":"OC-XXXXXXXXXXX","name":"Nicht Minna"},
        {"deviceTransitPolicyId":0000,"deviceId":"OC-XXXXXXXXXXX","name":"normal schedule"}
    ]]

    Fetching one policy:
    ["getDeviceTransitPolicy",{"deviceTransitPolicyId":0000}]
    Result:
    [{"deviceTransitPolicyId":0000,
        "deviceId":"OC-XXXXXXXXXXX",
        "name":"Nachts",
        "transitPolicy":{
            "rules":[
                {"action":{"lock":true},"criteria":{"eventTriggerSource":3,"eventClassification":[2,3]},"description":"Contraband Rule"},
                {"action":{"lock":false},"enabled":true,"criteria":{"rfidCode":["000000000000003","000000000000001","000000000000002"],"eventTriggerSource":3},"description":"Entry Rule"}],
            "idleLock":true,
            "idleLockBattery":true
        }
    }]

    Activating a policy:
    ["activateDeviceTransitPolicy",{"deviceId":"OC-XXXXXXXXXXX","deviceTransitPolicyId":0000}]
    Response:
    [{"deviceTransitPolicyId":0000,
        "deviceId":"OC-XXXXXXXXXXX",
        "name":"normal schedule",
        "transitPolicy":{
            "rules":[
                {"action":{"lock":false},"enabled":true,"criteria":{"rfidCode":["000000000000001","000000000000002","000000000000003"],"timeRange":"07:00-16:30","eventTriggerSource":2},"description":"Exit Rule"},
                {"action":{"lock":true},"criteria":{"eventTriggerSource":3,"eventClassification":[2,3]},"description":"Contraband Rule"},
                {"action":{"lock":false},"enabled":true,"criteria":{"rfidCode":["000000000000001","000000000000002","000000000000003"],"eventTriggerSource":3},"description":"Entry Rule"}],
            "idleLock":true,
            "idleLockBattery":true}}]
    """  # noqa: E501

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "onlycat_policy_select"

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
        policies: list[dict],
        entity_description: SelectEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._state = None
        self._attr_raw_data = None
        self._api_client = api_client
        self._attr_name = "Policy"
        self._attr_unique_id = device["deviceId"].replace("-", "_").lower() + "_policy"
        self.entity_id = "select." + self._attr_unique_id
        self._attr_options = [policy["name"] for policy in policies]
        self.device = device
        self._policies = policies
        self.set_current_policy(device["deviceTransitPolicyId"])
        api_client.add_event_listener("deviceUpdate", self.on_device_update)

    def set_current_policy(self, policy: int) -> None:
        """Set the current policy."""
        _LOGGER.debug(
            "Setting policy %s for device %s", policy, self.device["deviceId"]
        )
        self._attr_current_option = next(
            p["name"] for p in self._policies if p["deviceTransitPolicyId"] == policy
        )

    async def on_device_update(self, data: dict) -> None:
        """Handle device update event."""
        _LOGGER.debug("Device update event received for select: %s", data)
        if data["deviceId"] != self.device["deviceId"]:
            return
        if "deviceTransitPolicyId" in data or (
            "body" in data and "deviceTransitPolicyId" in data["body"]
        ):
            if "deviceTransitPolicyId" in data:
                policy = data["deviceTransitPolicyId"]
            else:
                policy = data["body"]["deviceTransitPolicyId"]
            self.set_current_policy(policy)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Activate a device policy."""
        _LOGGER.debug(
            "Setting policy %s for device %s", option, self.device["deviceId"]
        )
        policy = next(
            p["deviceTransitPolicyId"] for p in self._policies if p["name"] == option
        )
        await self._api_client.send_message(
            "activateDeviceTransitPolicy",
            {"deviceId": self.device["deviceId"], "deviceTransitPolicyId": policy},
        )
