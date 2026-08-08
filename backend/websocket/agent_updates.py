from fastapi import WebSocket


class AgentUpdateHub:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, payload: dict):
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_threadsafe(self, payload: dict, loop=None):
        """Thread-safe way to broadcast from a synchronous worker."""
        import asyncio
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # We are likely in a thread with no loop, but we need the main one.
                # In most AgriNegotiator setups, we pass the loop explicitly.
                return

        asyncio.run_coroutine_threadsafe(self.broadcast(payload), loop)


agent_update_hub = AgentUpdateHub()
