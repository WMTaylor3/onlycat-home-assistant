"""
Custom integration to integrate OnlyCat with Home Assistant.

For more details about this integration, please refer to
https://github.com/OnlyCatAI/onlycat-home-assistant
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OnlyCatApiClient
from .data.__init__ import OnlyCatConfigEntry, OnlyCatData
from .data.device import Device, DeviceUpdate
from .data.event import Event
from .data.pet import Pet
from .data.policy import DeviceTransitPolicy
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.DEVICE_TRACKER,
    Platform.BUTTON,
    Platform.SENSOR,
]
_LOGGER = logging.getLogger(__name__)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnlyCatConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    entry.runtime_data = OnlyCatData(
        client=OnlyCatApiClient(
            token=entry.data["token"],
            session=async_get_clientsession(hass),
        ),
        devices=[],
        pets=[],
    )
    await entry.runtime_data.client.connect()

    await _initialize_devices(entry)
    await _initialize_pets(entry)

    async def refresh_subscriptions(args: dict | None) -> None:
        _LOGGER.debug("Refreshing subscriptions, caused by event: %s", args)
        for device in entry.runtime_data.devices:
            await entry.runtime_data.client.send_message(
                "getDevice", {"deviceId": device.device_id, "subscribe": True}
            )
            await entry.runtime_data.client.send_message(
                "getDeviceEvents", {"deviceId": device.device_id, "subscribe": True}
            )

    async def update_device(data: dict) -> None:
        """Update a device in our runtime data when it is changed."""
        update = DeviceUpdate.from_api_response(data)

        for device in entry.runtime_data.devices:
            if device.device_id == update.device_id:
                updated_device = Device.from_api_response(
                    await entry.runtime_data.client.send_message(
                        "getDevice", {"deviceId": update.device_id, "subscribe": True}
                    )
                )
                device.update_from(updated_device)
                await _retrieve_device_transit_policies(entry, device)
                _LOGGER.debug("Updated device: %s", device)
                break
        else:
            _LOGGER.warning(
                "Device with ID %s not found in runtime data", update.device_id
            )

    async def subscribe_to_device_event(data: dict) -> None:
        """Subscribe to a device event to get updates about the event in the future."""
        await entry.runtime_data.client.send_message(
            "getEvent",
            {
                "deviceId": data["deviceId"],
                "eventId": data["eventId"],
                "subscribe": True,
            },
        )

    await refresh_subscriptions(None)
    entry.runtime_data.client.add_event_listener("connect", refresh_subscriptions)
    entry.runtime_data.client.add_event_listener("userUpdate", refresh_subscriptions)
    entry.runtime_data.client.add_event_listener("deviceUpdate", update_device)
    entry.runtime_data.client.add_event_listener(
        "deviceEventUpdate", subscribe_to_device_event
    )

    await async_setup_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def _initialize_devices(entry: OnlyCatConfigEntry) -> None:
    device_ids = (
        device["deviceId"]
        for device in await entry.runtime_data.client.send_message(
            "getDevices", {"subscribe": True}
        )
    )
    for device_id in device_ids:
        device = Device.from_api_response(
            await entry.runtime_data.client.send_message(
                "getDevice", {"deviceId": device_id, "subscribe": True}
            )
        )
        entry.runtime_data.devices.append(device)

    for device in entry.runtime_data.devices:
        await _retrieve_device_transit_policies(entry, device)

async def _retrieve_device_transit_policies(
    entry: OnlyCatConfigEntry, device: Device
) -> None:
    resp = await entry.runtime_data.client.send_message(
        "getDeviceTransitPolicies", {"deviceId": device.device_id}
    )
    if not resp:
        return []
    
    # First populate a list of IDs
    policy_ids: list[int] = []    
    for item in resp:
        pid = item.get("deviceTransitPolicyId")
        if pid is None:
            continue
        policy_ids.append(pid)
    
    # Then fetch full policy details in parallel
    if not policy_ids:
        return []
    
    coros = [
        entry.runtime_data.client.send_message(
            "getDeviceTransitPolicy",
            {"deviceTransitPolicyId": pid}
        )
        for pid in policy_ids
    ]
    responses = await asyncio.gather(*coros, return_exceptions=True)
    policies: list[DeviceTransitPolicy] = []
    for pid, res in zip(policy_ids, responses):
        if isinstance(res, Exception):
            _LOGGER.warning(
                "Failed to load policy %s for device %s: %s", pid, device.device_id, res
            )
            continue
        policy = DeviceTransitPolicy.from_api_response(res)
        policy.device = device
        if policy is not None:
            policies.append(policy)
    
    device.device_transit_policies = policies

async def _initialize_pets(entry: OnlyCatConfigEntry) -> None:
    for device in entry.runtime_data.devices:
        events = [
            Event.from_api_response(event)
            for event in await entry.runtime_data.client.send_message(
                "getDeviceEvents", {"deviceId": device.device_id}
            )
        ]
        rfids = await entry.runtime_data.client.send_message(
            "getLastSeenRfidCodesByDevice", {"deviceId": device.device_id}
        )
        for rfid in rfids:
            rfid_code = rfid["rfidCode"]
            last_seen = datetime.fromisoformat(rfid["timestamp"])
            rfid_profile = await entry.runtime_data.client.send_message(
                "getRfidProfile", {"rfidCode": rfid_code}
            )
            label = rfid_profile.get("label")
            pet = Pet(device, rfid_code, last_seen, label=label)
            _LOGGER.debug(
                "Found Pet %s for device %s",
                label if label else rfid_code,
                device.device_id,
            )
            entry.runtime_data.pets.append(pet)

            # Get last seen event to determine current presence state
            for event in events:
                if event.rfid_codes and pet.rfid_code in event.rfid_codes:
                    pet.last_seen_event = event
                    break


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OnlyCatConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OnlyCatConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
