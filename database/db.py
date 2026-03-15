"""
database/db.py — SQLite-backed persistence layer.

Public ``Database`` class keeps the same class-method API as the old
in-memory version so that no other files need to change.  Data is
persisted in ``agrinegotiator.db`` (configurable via DB_PATH env var).
"""

import os
import sqlite3
import json
from copy import deepcopy
from uuid import uuid4

DB_PATH = os.getenv("DB_PATH", "agrinegotiator.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT,
    location TEXT,
    language TEXT
);

CREATE TABLE IF NOT EXISTS farmers (
    id TEXT PRIMARY KEY,
    name TEXT,
    location TEXT,
    language TEXT
);

CREATE TABLE IF NOT EXISTS buyers (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produce (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS negotiations (
    negotiation_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offers (
    id TEXT PRIMARY KEY,
    negotiation_id TEXT,
    round_num INTEGER,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    data TEXT NOT NULL
);
"""


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _init_db():
    with _conn() as c:
        c.executescript(_SCHEMA)


_init_db()


class Database:
    """
    Thin SQLite wrapper that mimics the previous dict-based API.

    For simple / hackathon use it also maintains in-memory caches
    (``Database.users``, ``Database.buyers``, etc.) populated lazily,
    so that code reading those class-attributes still works.
    """

    # ── In-memory mirrors (populated lazily) ───────────────────────
    users: dict = {}
    farmers: dict = {}
    buyers: dict = {}
    produce: dict = {}
    negotiations: dict = {}
    offers: dict = {}
    contracts: dict = {}
    history: dict = {}

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:8]}"

    @classmethod
    def reset(cls):
        """Wipe everything (used in tests)."""
        with _conn() as c:
            for tbl in ("users", "farmers", "buyers", "produce",
                        "negotiations", "offers", "contracts", "history"):
                c.execute(f"DELETE FROM {tbl}")
        cls.users = {}
        cls.farmers = {}
        cls.buyers = {}
        cls.produce = {}
        cls.negotiations = {}
        cls.offers = {}
        cls.contracts = {}
        cls.history = {}

    # ── Users ────────────────────────────────────────────────────────

    @classmethod
    def upsert_user(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                (p["user_id"], p.get("name"), p.get("email"),
                 p.get("password"), p.get("location"), p.get("language")),
            )
        cls.users[p["user_id"]] = p
        return p

    @classmethod
    def _load_users(cls):
        with _conn() as c:
            rows = c.execute("SELECT * FROM users").fetchall()
        cls.users = {r["user_id"]: dict(r) for r in rows}

    # ── Farmers ──────────────────────────────────────────────────────

    @classmethod
    def upsert_farmer(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        farmer_id = p.get("id") or cls.generate_id("farmer")
        p["id"] = farmer_id
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO farmers VALUES (?,?,?,?)",
                (farmer_id, p.get("name"), p.get("location"), p.get("language")),
            )
        cls.farmers[farmer_id] = p
        return p

    # ── Buyers ───────────────────────────────────────────────────────

    @classmethod
    def upsert_buyer(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        buyer_id = p.get("id") or cls.generate_id("buyer")
        p["id"] = buyer_id
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO buyers VALUES (?,?)",
                (buyer_id, json.dumps(p)),
            )
        cls.buyers[buyer_id] = p
        return p

    @classmethod
    def list_buyers(cls) -> list:
        if not cls.buyers:
            with _conn() as c:
                rows = c.execute("SELECT data FROM buyers").fetchall()
            cls.buyers = {
                json.loads(r["data"])["id"]: json.loads(r["data"]) for r in rows
            }
        return list(cls.buyers.values())

    # ── Produce ──────────────────────────────────────────────────────

    @classmethod
    def create_produce(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("produce")
        with _conn() as c:
            c.execute(
                "INSERT INTO produce VALUES (?,?)",
                (p["id"], json.dumps(p)),
            )
        cls.produce[p["id"]] = p
        return p

    @classmethod
    def list_produce(cls) -> list:
        with _conn() as c:
            rows = c.execute("SELECT data FROM produce").fetchall()
        result = [json.loads(r["data"]) for r in rows]
        cls.produce = {p["id"]: p for p in result}
        return result

    # ── Negotiations ─────────────────────────────────────────────────

    @classmethod
    def create_negotiation(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        neg_id = p.get("negotiation_id") or cls.generate_id("neg")
        p["negotiation_id"] = neg_id
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO negotiations VALUES (?,?)",
                (neg_id, json.dumps(p)),
            )
        cls.negotiations[neg_id] = p
        return p

    @classmethod
    def update_negotiation(cls, neg_id: str, payload: dict):
        payload["negotiation_id"] = neg_id
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO negotiations VALUES (?,?)",
                (neg_id, json.dumps(payload)),
            )
        cls.negotiations[neg_id] = payload

    # ── Offers ───────────────────────────────────────────────────────

    @classmethod
    def append_offer(cls, negotiation_id: str, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("offer")
        p["negotiation_id"] = negotiation_id
        with _conn() as c:
            c.execute(
                "INSERT INTO offers VALUES (?,?,?,?)",
                (p["id"], negotiation_id, p.get("round", 0), json.dumps(p)),
            )
        cls.offers[p["id"]] = p
        return p

    @classmethod
    def get_offers_for_negotiation(cls, negotiation_id: str) -> list:
        with _conn() as c:
            rows = c.execute(
                "SELECT data FROM offers WHERE negotiation_id=? ORDER BY round_num",
                (negotiation_id,),
            ).fetchall()
        return [json.loads(r["data"]) for r in rows]

    # ── Contracts ────────────────────────────────────────────────────

    @classmethod
    def create_contract(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("contract")
        with _conn() as c:
            c.execute(
                "INSERT INTO contracts VALUES (?,?)",
                (p["id"], json.dumps(p)),
            )
        cls.contracts[p["id"]] = p
        return p

    # ── History ──────────────────────────────────────────────────────

    @classmethod
    def add_history(cls, user_id: str, entry: dict):
        record_id = cls.generate_id("hist")
        entry = deepcopy(entry)
        entry["user_id"] = user_id
        with _conn() as c:
            c.execute(
                "INSERT INTO history VALUES (?,?,?)",
                (record_id, user_id, json.dumps(entry)),
            )
        if user_id not in cls.history:
            cls.history[user_id] = []
        cls.history[user_id].append(entry)

    @classmethod
    def get_history(cls, user_id: str = "all") -> list:
        with _conn() as c:
            if user_id == "all":
                rows = c.execute(
                    "SELECT data FROM history ORDER BY rowid DESC LIMIT 50"
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT data FROM history WHERE user_id=? ORDER BY rowid DESC",
                    (user_id,),
                ).fetchall()
        return [json.loads(r["data"]) for r in rows]
