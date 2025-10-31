"""Custom types for onlycat representing transit policies."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from .event import Event, EventClassification, EventTriggerSource

if TYPE_CHECKING:
    from collections.abc import Callable

    from .device import Device

_LOGGER = logging.getLogger(__name__)


def map_api_list_or_obj(api_obj: list | object, mapper: Callable) -> list | None:
    """Map a single object or list of objects from the API using the mapper function."""
    if isinstance(api_obj, list):
        return [mapper(obj) for obj in api_obj]
    if api_obj:
        return [mapper(api_obj)]
    return None


class PolicyResult(Enum):
    """Enum representing the result of a policy given a specific event."""

    UNKNOWN = 0
    LOCKED = 1
    UNLOCKED = 2


class SoundAction(StrEnum):
    """Enum representing the sound actions available in a transit policy rule."""

    UNKNOWN = "unknown"
    AFFIRM = "affirm"
    ALARM = "alarm"
    ANGRY_MEOW = "angry-meow"
    BELL = "bell"
    CHOIR = "choir"
    COIN = "coin"
    DENY = "deny"
    FANFARE = "fanfare"
    SUCCESS = "success"

    @classmethod
    def _missing_(cls, value: str) -> SoundAction:
        """Handle missing enum values in case of API extensions."""
        _LOGGER.warning("Unknown sound action: %s", value)
        return cls.UNKNOWN


@dataclass
class RuleAction:
    """Data representing an action in a transit policy rule."""

    lock: bool
    lockout_duration: int
    sound: SoundAction | None = None

    @classmethod
    def from_api_response(cls, api_action: dict) -> RuleAction | None:
        """Create a RuleAction instance from API response data."""
        if api_action is None:
            return None

        sound = api_action.get("sound")

        return cls(
            lock=api_action.get("lock"),
            lockout_duration=api_action.get("lockoutDuration"),
            sound=SoundAction(sound) if sound else None,
        )
    
    def to_dict(self) -> dict:
        d = {"lock": self.lock, "lockoutDuration": self.lockout_duration}
        if self.sound is not None:
            d["sound"] = self.sound.value if hasattr(self.sound, "value") else str(self.sound)
        return d


@dataclass
class TimeRange:
    """Data representing a range of time when a rule criteria is active."""

    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

    @classmethod
    def from_api_response(cls, api_time_range: str) -> TimeRange | None:
        """Create a TimeRange instance from API response data."""
        if api_time_range is None:
            return None

        start_time, end_time = api_time_range.split("-")
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour, end_minute = map(int, end_time.split(":"))

        return cls(
            start_hour=start_hour,
            start_minute=start_minute,
            end_hour=end_hour,
            end_minute=end_minute,
        )
    
    def to_dict(self) -> str:
        return f"{self.start_hour:02d}:{self.start_minute:02d}-{self.end_hour:02d}:{self.end_minute:02d}"

    def contains_timestamp(self, timestamp: datetime, timezone: tzinfo) -> bool:
        """Check if the given timestamp is within this time range."""
        event_time = timestamp.astimezone(timezone)
        start_time = event_time.replace(
            hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0
        )
        end_time = event_time.replace(
            hour=self.end_hour, minute=self.end_minute, second=59, microsecond=999999
        )

        # Handle overnight ranges (e.g., 22:00-02:00)
        if start_time > end_time:
            if start_time > event_time:
                start_time = start_time - timedelta(days=1)
            else:
                end_time = end_time + timedelta(days=1)

        return start_time <= event_time <= end_time


@dataclass
class RuleCriteria:
    """Data representing criteria for a rule in a transit policy."""

    event_trigger_sources: list[EventTriggerSource]
    event_classifications: list[EventClassification]
    time_ranges: list[TimeRange]
    rfid_codes: list[str]
    rfid_timeout: int

    @classmethod
    def from_api_response(cls, api_criteria: dict) -> RuleCriteria | None:
        """Create a RuleCriteria instance from API response data."""
        if api_criteria is None:
            return None

        trigger_source = map_api_list_or_obj(
            api_criteria.get("eventTriggerSource"), lambda x: EventTriggerSource(x)
        )
        classification = map_api_list_or_obj(
            api_criteria.get("eventClassification"), lambda x: EventClassification(x)
        )
        time_range = map_api_list_or_obj(
            api_criteria.get("timeRange"), lambda x: TimeRange.from_api_response(x)
        )
        rfid_code = map_api_list_or_obj(api_criteria.get("rfidCode"), lambda x: x)

        return cls(
            event_trigger_sources=trigger_source,
            event_classifications=classification,
            time_ranges=time_range,
            rfid_codes=rfid_code,
            rfid_timeout=api_criteria.get("rfidTimeout"),
        )

    def to_dict(self) -> dict:
        def pack_list(v):
            if v is None:
                return None
            vals = [x.value if hasattr(x, "value") else x for x in v]
            return vals[0] if len(vals) == 1 else vals

        out: dict = {}
        ets = pack_list(self.event_trigger_sources)
        if ets is not None:
            out["eventTriggerSource"] = ets
        ecs = pack_list(self.event_classifications)
        if ecs is not None:
            out["eventClassification"] = ecs
        if self.time_ranges:
            tr = [t.to_dict() for t in self.time_ranges]
            out["timeRange"] = tr[0] if len(tr) == 1 else tr
        if self.rfid_codes:
            out["rfidCode"] = self.rfid_codes[0] if len(self.rfid_codes) == 1 else self.rfid_codes
        if self.rfid_timeout is not None:
            out["rfidTimeout"] = self.rfid_timeout
        return out
    
    def matches(self, event: Event, timezone: tzinfo) -> bool:
        """Check if the event matches the criteria of this rule."""
        if (
            self.event_trigger_sources
            and event.event_trigger_source not in self.event_trigger_sources
        ):
            return False

        if (
            self.event_classifications
            and event.event_classification not in self.event_classifications
        ):
            return False

        if self.rfid_codes and not any(
            code in self.rfid_codes for code in event.rfid_codes
        ):
            return False

        return not self.time_ranges or any(
            time_range.contains_timestamp(event.timestamp, timezone)
            for time_range in self.time_ranges
        )


@dataclass
class Rule:
    """Data representing a rule in a transit policy."""

    action: RuleAction
    criteria: RuleCriteria
    description: str
    enabled: bool | None

    @classmethod
    def from_api_rule(cls, api_rule: dict) -> Rule | None:
        """Create a Rule instance from API response data."""
        if api_rule is None:
            return None

        return cls(
            action=RuleAction.from_api_response(api_rule.get("action")),
            criteria=RuleCriteria.from_api_response(api_rule.get("criteria")),
            description=api_rule.get("description"),
            enabled=api_rule.get("enabled", True),  # Default to True if not specified
        )
    
    def to_dict(self) -> dict:
        return {
            "criteria": self.criteria.to_dict() if self.criteria else None,
            "action": self.action.to_dict() if self.action else None,
            "description": self.description,
            "enabled": self.enabled,
        }


@dataclass
class TransitPolicy:
    """Data representing a transit policy for an OnlyCat device."""

    rules: list[Rule]
    idle_lock: bool
    idle_lock_battery: bool

    @classmethod
    def from_api_response(cls, api_policy: dict) -> TransitPolicy | None:
        """Create a TransitPolicy instance from API response data."""
        if api_policy is None:
            return None

        rules = api_policy.get("rules")

        return cls(
            rules=[Rule.from_api_rule(rule) for rule in rules] if rules else None,
            idle_lock=api_policy.get("idleLock"),
            idle_lock_battery=api_policy.get("idleLockBattery"),
        )
    
    def to_dict(self) -> dict:
        return {
            "rules": [r.to_dict() for r in self.rules] if self.rules else [],
            "idleLock": self.idle_lock,
            "idleLockBattery": self.idle_lock_battery,
        }


@dataclass
class DeviceTransitPolicy:
    """Data representing a transit policy for an OnlyCat device."""

    device_transit_policy_id: int
    device_id: str
    name: str | None = None
    transit_policy: TransitPolicy | None = None
    device: Device | None = None

    @classmethod
    def from_api_response(cls, api_policy: dict) -> DeviceTransitPolicy | None:
        """Create a DeviceTransitPolicy instance from API response data."""
        if api_policy is None or "deviceTransitPolicyId" not in api_policy:
            return None

        return cls(
            device_transit_policy_id=api_policy["deviceTransitPolicyId"],
            device_id=api_policy["deviceId"],
            name=api_policy.get("name"),
            transit_policy=TransitPolicy.from_api_response(
                api_policy.get("transitPolicy")
            ),
        )
    
    def to_dict(self) -> dict:
        return {
            "deviceTransitPolicyId": self.device_transit_policy_id,
            "deviceId": self.device_id,
            "name": self.name,
            "transitPolicy": self.transit_policy.to_dict() if self.transit_policy else None,
        }

    def determine_policy_result(self, event: Event) -> PolicyResult:
        """Determine the policy result for a given event."""
        if not self.transit_policy:
            _LOGGER.warning(
                "No transit policy set, unable to determine policy result for event %s",
                event.event_id,
            )
            return PolicyResult.UNKNOWN

        if self.transit_policy.rules:
            for rule in self.transit_policy.rules:
                if not rule.criteria or not rule.criteria.matches(
                    event, self.device.time_zone
                ):
                    continue
                result = (
                    PolicyResult.LOCKED if rule.action.lock else PolicyResult.UNLOCKED
                )
                _LOGGER.debug(
                    "Rule %s matched for event %s, result is: %s",
                    rule,
                    event.event_id,
                    result,
                )
                return result

        _LOGGER.debug(
            "No matching rules found for event %s, result is equal to idle lock: %s",
            event.event_id,
            self.transit_policy.idle_lock,
        )
        return (
            PolicyResult.LOCKED
            if self.transit_policy.idle_lock
            else PolicyResult.UNLOCKED
        )
