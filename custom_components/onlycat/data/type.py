"""Custom types for onlycat representing a type."""

from __future__ import annotations

import logging
from enum import StrEnum

_LOGGER = logging.getLogger(__name__)


class Type(StrEnum):
    """Enum representing the type of event received via SocketIO."""

    UNKNOWN = "unknown"
    CREATE = "create"
    UPDATE = "update"

    @classmethod
    def _missing_(cls, value: str) -> Type:
        """Handle missing enum values in case of API extensions."""
        _LOGGER.warning("Unknown type: %s", value)
        return cls.UNKNOWN
