import asyncio
import websockets

async def listen():

    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        while True:
            message = await websocket.recv()
            print("Received:", message)

asyncio.run(listen())