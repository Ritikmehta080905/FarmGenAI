from datetime import datetime, timezone

from database.db import Database


ROLE_OFFER_USER_ID = "role_offers"


def create_role_offer(payload: dict):
    role = str(payload.get("role", "")).strip().lower()
    if role not in {"buyer", "warehouse", "transporter", "processor", "compost"}:
        raise ValueError("Unsupported role for offer creation")

    quantity = float(payload.get("quantity", 0) or 0)
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    offered_price = payload.get("offered_price")
    if offered_price is not None:
        offered_price = float(offered_price)
        if offered_price <= 0:
            raise ValueError("offered_price must be greater than 0 when provided")

    record = {
        "id": Database.generate_id("role_offer"),
        "owner_user_id": payload.get("user_id"),
        "role": role,
        "actor_name": payload.get("actor_name", role.title()),
        "crop": payload.get("crop", "Produce"),
        "quantity": quantity,
        "offered_price": offered_price,
        "location": payload.get("location", "Unknown"),
        "notes": payload.get("notes", ""),
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    Database.add_history(ROLE_OFFER_USER_ID, {"type": "ROLE_OFFER", **record})
    return record


def list_role_offers(role: str | None = None, user_id: str | None = None):
    entries = Database.get_history(ROLE_OFFER_USER_ID)
    offers = [entry for entry in entries if entry.get("type") == "ROLE_OFFER"]

    if role:
        offers = [entry for entry in offers if str(entry.get("role", "")).lower() == str(role).lower()]

    if user_id:
        offers = [
            entry for entry in offers
            if (entry.get("owner_user_id") or entry.get("user_id")) == user_id
        ]

    offers.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return offers
