"""Button platform for OnlyCat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .button_reboot import OnlyCatRebootButton
from .button_unlock import OnlyCatUnlockButton

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data.__init__ import OnlyCatConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OnlyCatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform entities."""
    async_add_entities(
        button
        for device in entry.runtime_data.devices
        for button in (
            OnlyCatUnlockButton(
                device=device,
                api_client=entry.runtime_data.client,
            ),
            OnlyCatRebootButton(device=device, api_client=entry.runtime_data.client),
        )
    )
