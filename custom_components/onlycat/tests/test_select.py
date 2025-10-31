"""Test of OnlyCat Policy Select entity."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.select import SelectEntityDescription

from custom_components.onlycat import Device
from custom_components.onlycat.select_active_door_policy import OnlyCatPolicySelect, load_policies

get_device_transit_policies = [
    [],
    [
        {"deviceTransitPolicyId": 0, "deviceId": "OC-00000000001", "name": "Policy1"},
        {"deviceTransitPolicyId": 1, "deviceId": "OC-00000000001", "name": "Policy2"},
        {"deviceTransitPolicyId": 2, "deviceId": "OC-00000000001", "name": "Policy3"},
    ],
]


@pytest.mark.asyncio
@pytest.mark.parametrize("data", get_device_transit_policies)
async def test_load_policies(data: list) -> None:
    """Test loading policies for a device."""
    mock_client = AsyncMock()
    mock_client.send_message.side_effect = [data]
    device_id = "OC-00000000001"

    policies = await load_policies(mock_client, device_id)

    # Verify API call
    mock_client.send_message.assert_called_once_with(
        "getDeviceTransitPolicies", {"deviceId": device_id}
    )

    # Verify results
    assert len(policies) == len(data)


def test_empty_onlycat_policy_slect() -> None:
    """Tests initialization of OnlyCatPolicySelect with no active or known policies."""
    mock_device = Device(
        device_id="OC-00000000001",
        description="Test Cat Flap",
        device_transit_policy_id=None,
    )
    entity_description = SelectEntityDescription(
        key="onlycat_policy_select",
    )
    mock_api_client = AsyncMock()
    select = OnlyCatPolicySelect(
        device=mock_device,
        policies=[],
        entity_description=entity_description,
        api_client=mock_api_client,
    )

    assert select.device.device_id == "OC-00000000001"
