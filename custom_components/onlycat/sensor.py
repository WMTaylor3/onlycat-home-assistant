"""Sensor platform for OnlyCat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
import logging
_LOGGER = logging.getLogger(__name__)

from .api import OnlyCatApiClient

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import OnlyCatConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="onlycat",
        name="OnlyCat Sensor",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        OnlyCatSensor(
            entity_description=entity_description,
            api_client = entry.runtime_data.client,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )
    await entry.runtime_data.client.send_message("getDevice", {"deviceId":"OC-xxx","subscribe": True})
    # TODO: For testing. getting no responses
    await entry.runtime_data.client.send_message("getDevices", { "subscribe": True})
    await entry.runtime_data.client.send_message("getEvents", { "subscribe": True})
    #await entry.runtime_data.client.send_message("runDeviceCommand", {"deviceId":"OC-xxx","command":"unlock"})




class OnlyCatSensor(SensorEntity):
    """OnlyCat Sensor class."""

    def __init__(
        self,
        entity_description: SensorEntityDescription,
        api_client: OnlyCatApiClient,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._state = None
        self._attr_data = None
        api_client.add_event_listener("deviceUpdate", self.on_device_update)

    async def on_device_update(self, data: dict) -> None:
        """Handle device update event."""
        _LOGGER.debug("Device update event received: %s", data)
        self._state = True
        self._attr_data = str(data)

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self._state

    @property 
    def data(self) -> str | None:
        return self._attr_data