"""Custom types for onlycat representing a pet."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .event import EventTriggerSource
from .policy import PolicyResult

if TYPE_CHECKING:
    from datetime import datetime

    from .device import Device
    from .event import Event

_LOGGER = logging.getLogger(__name__)


@dataclass
class Pet:
    """Data representing a pet."""

    device: Device
    rfid_code: str
    last_seen: datetime
    last_seen_event: Event | None = None
    label: str | None = None

    def is_present(self, event: Event) -> bool | None:
        """Determine whether a pet is present based on an event."""
        pet_name = self.label if self.label else self.rfid_code
        if not self.device.device_transit_policy:
            _LOGGER.debug(
                "No transit policy set, unable to determine policy result for event %s",
                event.event_id,
            )
            return None
        if event.event_trigger_source not in (
            EventTriggerSource.OUTDOOR_MOTION,
            EventTriggerSource.INDOOR_MOTION,
        ):
            _LOGGER.debug("Event was not triggered by motion, ignoring event.")
            return None

        policy_result = self.device.device_transit_policy.determine_policy_result(event)
        if policy_result == PolicyResult.LOCKED:
            _LOGGER.debug("Transit was not allowed, ignoring event for %s.", pet_name)
            return None
        if policy_result == PolicyResult.UNKNOWN:
            _LOGGER.debug(
                "Unable to determine policy result, ignoring event for %s.",
                pet_name,
            )
            return None
        if event.event_trigger_source == EventTriggerSource.OUTDOOR_MOTION:
            _LOGGER.debug(
                "Transit allowed for outdoor motion, assuming %s is present.",
                pet_name,
            )
            return True
        _LOGGER.debug(
            "Transit allowed for indoor motion, assuming %s is not present.",
            pet_name,
        )
        return False
