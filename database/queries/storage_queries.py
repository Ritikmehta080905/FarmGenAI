"""Query helpers for warehouse / storage operations."""

from database.db import Database


def log_storage_event(neg_id: str, crop: str, quantity: float, cost: float):
    """Record a storage event as a history entry."""
    entry = {
        "type": "storage",
        "negotiation_id": neg_id,
        "crop": crop,
        "quantity": quantity,
        "cost": cost,
    }
    Database.add_history("all", entry)
    return entry


def get_storage_events() -> list:
    return [
        e for e in Database.get_history("all")
        if e.get("type") == "storage"
    ]
