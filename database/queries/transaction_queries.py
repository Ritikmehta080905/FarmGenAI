"""Query helpers for completed deal transactions."""

from database.db import Database


def create_contract(payload: dict) -> dict:
    return Database.create_contract(payload)


def list_contracts() -> list:
    return list(Database.contracts.values())


def add_transaction_history(user_id: str, entry: dict):
    Database.add_history(user_id, entry)


def get_transaction_history(user_id: str = "all") -> list:
    return Database.get_history(user_id)
