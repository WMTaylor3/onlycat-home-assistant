"""Custom types for onlycat representing a Device."""

from __future__ import annotations

import logging
import zoneinfo
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo
from typing import TYPE_CHECKING

from .type import Type

if TYPE_CHECKING:
    from .policy import DeviceTransitPolicy

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceConnectivity:
    """Data representing the connectivity of an OnlyCat device."""

    connected: bool
    disconnect_reason: str
    timestamp: datetime

    @classmethod
    def from_api_response(cls, api_connectivity: dict) -> DeviceConnectivity | None:
        """Create a DeviceConnectivity instance from API response data."""
        if api_connectivity is None:
            return None

        return cls(
            connected=api_connectivity.get("connected"),
            disconnect_reason=api_connectivity.get("disconnectReason"),
            timestamp=datetime.fromtimestamp(
                api_connectivity.get("timestamp") / 1000.0, tz=UTC
            ),
        )


@dataclass
class Device:
    """Data representing an OnlyCat device."""

    device_id: str
    connectivity: DeviceConnectivity | None = None
    description: str | None = None
    time_zone: tzinfo | None = None
    device_transit_policy_id: int | None = None
    device_transit_policy: DeviceTransitPolicy | None = None

    @classmethod
    def from_api_response(cls, api_device: dict) -> Device | None:
        """Create a Device instance from API response data."""
        if api_device is None:
            return None

        timezone_str = api_device.get("timeZone")
        if timezone_str is not None:
            try:
                timezone = zoneinfo.ZoneInfo(timezone_str)
            except zoneinfo.ZoneInfoNotFoundError:
                _LOGGER.warning("Unable to parse timezone: %s", timezone_str)
                timezone = UTC
        else:
            timezone = UTC

        return cls(
            device_id=api_device["deviceId"],
            connectivity=DeviceConnectivity.from_api_response(
                api_device.get("connectivity")
            ),
            time_zone=timezone,
            description=api_device.get("description"),
            device_transit_policy_id=api_device.get("deviceTransitPolicyId"),
        )

    def update_from(self, updated_device: Device) -> None:
        """Update the device with data from another Device instance."""
        if updated_device is None:
            return

        self.connectivity = updated_device.connectivity or self.connectivity
        self.description = updated_device.description or self.description
        self.time_zone = updated_device.time_zone or self.time_zone
        self.device_transit_policy_id = (
            updated_device.device_transit_policy_id or self.device_transit_policy_id
        )


@dataclass
class DeviceUpdate:
    """Data representing an update to a device."""

    device_id: str
    type: Type
    body: Device

    @classmethod
    def from_api_response(cls, api_event: dict) -> DeviceUpdate | None:
        """Create a DeviceUpdate instance from API response data."""
        if api_event is None:
            return None

        return cls(
            device_id=api_event["deviceId"],
            type=Type(api_event["type"]) if api_event.get("type") else Type.UNKNOWN,
            body=Device.from_api_response(api_event.get("body")),
        )
