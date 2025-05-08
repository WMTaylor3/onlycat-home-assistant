"""Sensor platform for OnlyCat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .binary_sensor_connectivity import OnlyCatConnectionSensor
from .binary_sensor_event import OnlyCatEventSensor

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OnlyCatConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        sensor
        for device in entry.data["devices"]
        for sensor in (
            OnlyCatEventSensor(
                device=device,
                api_client=entry.runtime_data.client,
            ),
            OnlyCatConnectionSensor(
                device=device,
                api_client=entry.runtime_data.client,
            ),
        )
    )
