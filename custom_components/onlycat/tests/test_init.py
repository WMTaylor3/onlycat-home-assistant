from unittest.mock import AsyncMock, patch
import pytest
from typing import TYPE_CHECKING, Any

from custom_components.onlycat import _initialize_devices, _retrieve_current_transit_policy
from custom_components.onlycat.data.device import Device
from custom_components.onlycat.data.policy import DeviceTransitPolicy
from custom_components.onlycat.api import OnlyCatApiClient

getDevices = [
    # "Normal device"
    {
        "deviceId":"OC-00000000001",
        "description":"Device Name",
        "timeZone":"Europe/Zurich",
        "deviceTransitPolicyId":0000,
        "cursorId":0000
    },
    # Fresh device with no transit policy
    {
        "deviceId":"OC-00000000002",
        "description":"Device Name",
        "timeZone":"Europe/Zurich",
        "cursorId":0000
    }
]
getDevice = { 
    "OC-00000000001": {
        "deviceId":"OC-00000000001",
        "description":"Durins Tor",
        "timeZone":"Europe/Zurich",
        "deviceTransitPolicyId":0000,
        "connectivity": {
            "connected": True,
            "disconnectReason": None,
            "timestamp":1743841488269
        }
    },
    "OC-00000000002": {
        "deviceId":"OC-00000000002",
        "description":"Durins Tor",
        "timeZone":"Europe/Zurich",
        "connectivity": {
            "connected": True,
            "disconnectReason": None,
            "timestamp":1743841488269
        }
    }
}
getDeviceTransitPolicy = {
    0: {
        "deviceTransitPolicyId":0000,
        "deviceId":"OC-00000000001",
        "name":"Nachts",
        "transitPolicy": {
            "rules": [
                {
                    "action":{
                        "lock": True
                    },
                    "criteria":{
                        "eventTriggerSource":3,
                        "eventClassification":[2,3]
                    },
                    "description":"Contraband Rule"
                },
                {
                    "action":{
                        "lock": False
                    },
                    "enabled": True,
                    "criteria":{
                        "rfidCode":[
                            "000000000000003",
                            "000000000000001",
                            "000000000000002"
                        ],
                        "eventTriggerSource":3
                    },
                    "description":"Entry Rule"
                }
            ],
            "idleLock": True,
            "idleLockBattery":True
        }
    }
}

# Setup test device api responses
async def mock_send_message(topic: str, data: dict) -> Any | None:
    if topic == "getDevices": 
        return getDevices
    if topic == "getDevice":
        return getDevice[data["deviceId"]]
    if topic == "getDeviceTransitPolicy":
        return getDeviceTransitPolicy[data["deviceTransitPolicyId"]]


@pytest.mark.asyncio
async def test_initialize_devices():
    mock_entry = AsyncMock()
    mock_entry.runtime_data.devices = []
    mock_entry.runtime_data.client = AsyncMock()
    mock_entry.runtime_data.client.send_message.side_effect = mock_send_message
    with patch("custom_components.onlycat._retrieve_current_transit_policy") as mock_retrieve_current_transit_policy:
        await _initialize_devices(mock_entry)

    assert len(mock_entry.runtime_data.devices) == len(getDevices)
    mock_entry.runtime_data.client.send_message.assert_any_call(
        "getDevices", {"subscribe": True}
    )
    for device_id in getDevice:
        mock_entry.runtime_data.client.send_message.assert_any_call(
            "getDevice", {"deviceId": device_id, "subscribe": True}
        )
    assert mock_entry.runtime_data.devices[1].device_transit_policy_id == None
    assert mock_retrieve_current_transit_policy.call_count == 1
