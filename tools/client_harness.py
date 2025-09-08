#!/usr/bin/env python3

import os
import sys
import json
import asyncio
import argparse
import socketio

ONLYCAT_URL = "https://gateway.onlycat.com"

async def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Send a SocketIO event to OnlyCat API")
    parser.add_argument("event", help="Event name to send")
    parser.add_argument("data", nargs="?", default="{}", help="Optional JSON data payload")
    args = parser.parse_args()

    # Get token from environment
    token = os.getenv("ONLYCAT_TOKEN")
    if not token:
        print("Error: ONLYCAT_TOKEN environment variable is not set.")
        sys.exit(1)

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError:
        print("Error: Invalid JSON payload.")
        sys.exit(1)

    # Create socketio client
    sio = socketio.AsyncClient(
        reconnection=True,
        reconnection_attempts=0,
        reconnection_delay=10,
        reconnection_delay_max=10,
        ssl_verify=True,
    )

    @sio.on("*")
    async def on_any_event(event, data):
        print(f"Received event: {event} → {data}")

    # Connect and send
    try:
        await sio.connect(
            ONLYCAT_URL,
            transports=["websocket"],
            headers={"platform": "development", "device": "dev-cli"},
            auth={"token": token},
        )
        print("Connected to OnlyCat")

        response = await sio.call(args.event, data)
        print(f"Response from '{args.event}': {response}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
