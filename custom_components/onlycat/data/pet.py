"""Custom types for onlycat representing a pet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from .device import Device
    from .event import Event


@dataclass
class Pet:
    """Data representing a pet."""

    device: Device
    rfid_code: str
    last_seen: datetime
    last_seen_event: Event | None = None
    label: str | None = None
