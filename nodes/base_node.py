import os
import sqlite3
import json
import logging
from typing import Dict, Optional, List
from .p2p_protocol import MessageType, P2PMessage
from llm.llm_client import LLMClient

# Base directory for local node data
NODE_DATA_DIR = os.path.join(os.getcwd(), "node_storage")
if not os.path.exists(NODE_DATA_DIR):
    os.makedirs(NODE_DATA_DIR)

class BaseNode:
    def __init__(self, node_id: str, role: str):
        self.node_id = node_id
        self.role = role
        self.llm = LLMClient()
        self.db_path = os.path.join(NODE_DATA_DIR, f"{node_id}.db")
        self._init_local_db()
        logging.info(f"Initialized Decentralized Node: {node_id} ({role}) [LLM: {self.llm.enabled}]")

    def _init_local_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Local private state for each node
            conn.execute("""
            CREATE TABLE IF NOT EXISTS local_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)
            # Local history of P2P messages (received or sent)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS p2p_ledger (
                message_id TEXT PRIMARY KEY,
                timestamp TEXT,
                from_node TEXT,
                to_node TEXT,
                msg_type TEXT,
                data TEXT,
                signature TEXT
            )
            """)
            # Local assets (produce for farmers, budget for buyers)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS local_assets (
                asset_id TEXT PRIMARY KEY,
                data TEXT
            )
            """)

    def save_state(self, key: str, value: any):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO local_state VALUES (?,?)", (key, json.dumps(value)))

    def get_state(self, key: str) -> Optional[any]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM local_state WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def record_p2p_event(self, msg: P2PMessage):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO p2p_ledger VALUES (?,?,?,?,?,?,?)",
                (msg.message_id, msg.timestamp, msg.from_node, msg.to_node, msg.msg_type, json.dumps(msg.data), msg.signature)
            )

    def get_ledger(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM p2p_ledger ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    async def handle_message(self, msg: P2PMessage) -> Optional[P2PMessage]:
        """Override in role-specific nodes to implement local agent logic."""
        self.record_p2p_event(msg)
        return None
