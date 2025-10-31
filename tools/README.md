# Dev Tools

Contained within this folder are useful scripts for developing against the OnlyCat Cloud API.

## Setup
In each case you'll need to set your auth token as an environment variable by running the following in a terminal:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ chmod +x export ONLYCAT_TOKEN=your-token-here
```

After that, you'll need to set each script as being executible:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ chmod +x client_request_harness.py
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ chmod +x client_event_harness.py
```

You'll then be able to execute each of the scripts as needed.

## client_event_harness.py
This script is for subscribing to SocketIO events as they come down from the cloud API. This is essentially what the Mobile App receives.

Leave it running in the background in a terminal window with:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ ./client_event_harness.py
Received event: userUpdate →
{
  "id": 1234,
  "sub": "auth0|123456789qwerty",
  "email": "user@gmail.com",
  "name": "user@gmail.com",
  "description": null,
  "avatarUrl": "",
  "userLevel": null
}
Connected to OnlyCat — listening for events...
```

## client_request_harness.py
This script allows you to send requests to the cloud API. Some examples of its usages are as follows:

Getting a device details:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ ./client_request_harness.py getDevice '{"deviceId": "OC-123ABC123ABC"}'
Connected to OnlyCat
Response from 'getDevice':
{
  "deviceId": "OC-123ABC123ABC",
  "description": "Main",
  "timeZone": "Pacific/Auckland",
  "deviceTransitPolicyId": 123456,
  "connectivity": {
    "connected": false,
    "disconnectReason": "MQTT_KEEP_ALIVE_TIMEOUT",
    "timestamp": 1757324467381
  }
}
```

Requesting a list of transit policies:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ ./client_request_harness.py getDeviceTransitPolicies '{"deviceId": "OC-123ABC123ABC"}'
Connected to OnlyCat
Response from 'getDeviceTransitPolicies':
[
  {
    "deviceTransitPolicyId": 123456,
    "deviceId": "OC-123ABC123ABC",
    "name": "Unlock for All"
  },
  {
    "deviceTransitPolicyId": 456789,
    "deviceId": "OC-123ABC123ABC",
    "name": "Locked"
  }
]
```

Requesting details for a specific transit policy:
```sh
(venv) user@computer:~/Documents/GitHub/onlycat-home-assistant/tools$ ./client_request_harness.py getDeviceTransitPolicy '{"deviceTransitPolicyId": "123456"}'
Connected to OnlyCat
Response from 'getDeviceTransitPolicy':
{
  "deviceTransitPolicyId": 123456,
  "deviceId": "OC-123ABC123ABC",
  "name": "Locked",
  "transitPolicy": {
    "rules": [
      {
        "action": {
          "lock": true
        }
      }
    ],
    "idleLock": true,
    "idleLockBattery": true
  }
}
```

