
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import json
import websockets
from shared.event_bus import event_bus

connected_clients = set()

# Holds the event loop running the WebSocket server so that
# event_listener (called from the simulation thread) can schedule
# coroutines safely via run_coroutine_threadsafe.
_loop = None


async def handler(websocket):

    print("Frontend connected")

    connected_clients.add(websocket)

    try:
        async for _ in websocket:
            pass
    finally:
        connected_clients.discard(websocket)


async def broadcast(event):

    if not connected_clients:
        return

    message = json.dumps(event)

    await asyncio.gather(
        *[client.send(message) for client in connected_clients],
        return_exceptions=True
    )


def event_listener(event):

    print("EVENT:", event.get("type", str(event)))

    global _loop
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast(event), _loop)


async def start_server():

    global _loop
    _loop = asyncio.get_running_loop()

    event_bus.subscribe(event_listener)

    server = await websockets.serve(handler, "localhost", 8765)

    print("WebSocket running at ws://localhost:8765")

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())