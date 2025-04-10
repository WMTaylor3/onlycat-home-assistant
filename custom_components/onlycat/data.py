"""Custom types for onlycat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import OnlyCatApiClient


type OnlyCatConfigEntry = ConfigEntry[OnlyCatData]


@dataclass
class OnlyCatData:
    """Data for the OnlyCat integration."""

    client: OnlyCatApiClient
