"""
backend/workers/websocket_broadcaster.py

Subscribes to Redis Pub/Sub channels (e.g., `agri:ws:updates`) and forwards 
them to the active WebSocket clients connected to FastAPI.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger("WSBroadcaster")

class WebSocketBroadcaster:
    """Manages routing between Redis Pub/Sub and FastAPI WebSockets."""
    
    def __init__(self):
        self.pubsub_channel = "agri:ws:updates"
        # Reference to FastAPI ConnectionManager (mocked here)
        self.active_connections = {} 
        
    def listen_to_redis(self):
        """Blocking listener to consume UI update events from agents."""
        logger.info(f"Subscribed to Redis channel: {self.pubsub_channel}")
        # In production: redis.pubsub().subscribe(self.pubsub_channel)
        
    def handle_message(self, message: str):
        """Callback when a message arrives from Redis."""
        try:
            data = json.loads(message)
            target_user = data.get("user_id")
            payload = data.get("payload")
            
            self.send_to_client(target_user, payload)
        except json.JSONDecodeError:
            logger.error("Invalid WS message format.")
            
    def send_to_client(self, user_id: str, payload: Dict[str, Any]):
        """Push JSON payload down the active WebSocket connection."""
        if user_id in self.active_connections:
            ws = self.active_connections[user_id]
            # ws.send_json(payload)
            logger.info(f"Sent {payload} to user {user_id}")
        else:
            logger.debug(f"User {user_id} not connected to this pod.")

if __name__ == "__main__":
    broadcaster = WebSocketBroadcaster()
    broadcaster.listen_to_redis()
