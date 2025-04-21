"""
Custom integration to integrate OnlyCat with Home Assistant.

For more details about this integration, please refer to
https://github.com/OnlyCatAI/onlycat-home-assistant
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OnlyCatApiClient
from .data import OnlyCatConfigEntry, OnlyCatData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SELECT]


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
    )
    await entry.runtime_data.client.connect()
    for device in entry.data["devices"]:
        info = await entry.runtime_data.client.send_message(
            "getDevice", {"deviceId": device["deviceId"], "subscribe": True}
        )
        device.update(info)
    entry.runtime_data.devices = [
        device["deviceId"] for device in entry.data["devices"]
    ]

    async def refresh_subscriptions() -> None:
        for device in entry.runtime_data.devices:
            await entry.runtime_data.client.send_message(
                "getDevice", {"deviceId": device, "subscribe": True}
            )

    entry.runtime_data.client.add_event_listener("connect", refresh_subscriptions)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


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
