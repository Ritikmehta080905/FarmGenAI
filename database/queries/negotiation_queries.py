"""Query helpers for negotiations and offers."""

from database.db import Database


def create_negotiation(payload: dict) -> dict:
    return Database.create_negotiation(payload)


def get_negotiation(neg_id: str) -> dict | None:
    return Database.negotiations.get(neg_id)


def update_negotiation(neg_id: str, payload: dict):
    Database.update_negotiation(neg_id, payload)


def list_negotiations(limit: int = 50) -> list:
    return Database.get_history("all")[:limit]


def add_offer(neg_id: str, offer: dict) -> dict:
    return Database.append_offer(neg_id, offer)


def get_offers(neg_id: str) -> list:
    return Database.get_offers_for_negotiation(neg_id)
