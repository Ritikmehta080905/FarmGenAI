"""Query helpers for farmer / produce data."""

from database.db import Database


def get_all_produce() -> list:
    return Database.list_produce()


def get_produce_by_farmer(farmer_name: str) -> list:
    return [p for p in Database.list_produce() if p.get("farmer_name") == farmer_name]


def create_produce_listing(payload: dict) -> dict:
    return Database.create_produce(payload)


def get_all_buyers() -> list:
    return Database.list_buyers()
