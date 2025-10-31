#!/usr/bin/env python3

import os
import asyncio
import socketio

ONLYCAT_URL = "https://gateway.onlycat.com"

async def main():
    token = os.getenv("ONLYCAT_TOKEN")
    if not token:
        print("Error: ONLYCAT_TOKEN environment variable is not set.")
        return

    sio = socketio.AsyncClient(
        reconnection=True,
        reconnection_attempts=0,
        reconnection_delay=10,
        reconnection_delay_max=10,
        ssl_verify=True,
    )

    # Generic catch-all event handler
    @sio.on("*")
    async def on_any_event(event, data):
        print(f"Received event: {event} → {data}")

    try:
        await sio.connect(
            ONLYCAT_URL,
            transports=["websocket"],
            headers={"platform": "development", "device": "dev-events-harness"},
            auth={"token": token},
        )
        print("Connected to OnlyCat — listening for events...")

        # Keep the client running to receive events
        await sio.wait()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
