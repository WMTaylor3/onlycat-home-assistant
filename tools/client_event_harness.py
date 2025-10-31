#!/usr/bin/env python3

import os
import asyncio
import socketio
import json

ONLYCAT_URL = "https://gateway.onlycat.com"

async def main():
    token = os.getenv("ONLYCAT_TOKEN")
    if not token:
        print("Error: ONLYCAT_TOKEN environment variable is not set.")
        return

    sio = socketio.AsyncClient()

    async def refresh_subscriptions():
        print("Refreshing subscriptions...")
        await sio.emit("getDevices", {"subscribe": True})
        await sio.emit("getEvents", {"subscribe": True})
        await refresh_devices()

    async def refresh_devices():
        print("Refreshing devices...")

        try:
            devices = await sio.call("getDevices", {"subscribe": True})
        except Exception as e:
            print(f"Failed to fetch devices: {e}")
            return
        
        for device in devices:
            device_id = device["deviceId"]
            print(f" Subscribing to {device_id}")
            await sio.emit("getDevice", {"deviceId": device_id, "subscribe": True})
            await sio.emit("getDeviceEvents", {"deviceId": device_id, "subscribe": True})
            await sio.emit("getDeviceTransitPolicies", {"deviceId": device_id, "subscribe": True})

    @sio.on("connect")
    async def on_connect():
        print("Connected!")
        await refresh_subscriptions()

    @sio.on("userUpdate")
    async def on_user_update(data):
        print("userUpdate →")
        print(json.dumps(data, indent=2))
        await refresh_subscriptions()

    @sio.on("eventUpdate")
    async def on_device_update(data):
        print("eventUpdate →")
        print(json.dumps(data, indent=2))

    @sio.on("deviceUpdate")
    async def on_device_update(data):
        print("deviceUpdate →")
        print(json.dumps(data, indent=2))
        await refresh_devices()

    @sio.on("deviceEventUpdate")
    async def on_device_event_update(data):
        print("deviceEventUpdate →")
        print(json.dumps(data, indent=2))

        # Subscribe to updates about this specific event for this specific device
        await sio.emit("getEvent", {
            "deviceId": data["deviceId"],
            "eventId": data["eventId"],
            "subscribe": True
        })

    @sio.on("*")
    async def on_any_event(event, data):
        print(f"WILDCARD event: {event} →")
        print(json.dumps(data, indent=2))

    await sio.connect(
        ONLYCAT_URL,
        transports=["websocket"],
        headers={"platform": "development", "device": "dev-events-harness"},
        auth={"token": token},
    )

    print("Listening for all events...")
    await sio.wait()

if __name__ == "__main__":
    asyncio.run(main())
