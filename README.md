# onlycat-home-assistant

HomeAssistant integration for OnlyCat flaps.

## Features
1. Discover all flaps associated with one account
2. Show and allow to select active door policy (policies have to be created/modified via app)
3. Sensors for:
   * Flap connection status
   * Flap events (timestamp, RFID codes, trigger source, event classification)
   * Contraband detection
   * Lock state
4. Device Tracker for pet presence
5. Buttons for:
   * Reboot
   * Remote unlock
6. Services for:
   * Overriding a pets location (onlycat.set_pet_location)

## How to install
1. Install HACS
2. Add this repository to HACS via "Custom Repositories"
3. Install OnlyCat Integration

## Development

1. Install pip requirements via `pip install -r requirements.txt`
2. Run a HA instance:
   1. Directly by running `./scripts/develop`, or
   2. In Docker by running `docker run --volume ./config:/config --volume ./custom_components:/config/custom_components -p 8123:8123 "ghcr.io/home-assistant/home-assistant:stable"`
3. Add the integration from the HA "Devices & services" ui.

