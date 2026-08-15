from datetime import datetime, timezone

from database.db import Database


ROLE_OFFER_USER_ID = "role_offers"


async def create_role_offer(payload: dict):
    role = str(payload.get("role", "")).strip().lower()
    if role not in {"buyer", "warehouse", "transporter", "processor", "compost"}:
        raise ValueError("Unsupported role for offer creation")

    quantity = float(payload.get("quantity", 0) or 0)
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    min_price = float(payload.get("min_price", 0))
    max_price = float(payload.get("max_price", 0))

    if min_price <= 0:
        raise ValueError("min_price must be greater than 0")

    record = {
        "id": Database.generate_id("role_offer"),
        "user_id": payload.get("user_id"),
        "role": role,
        "actor_name": payload.get("actor_name", role.title()),
        "crop": payload.get("crop", "Produce"),
        "quantity": quantity,
        "min_price": min_price,
        "max_price": max_price,
        "offered_price": max_price,  # baseline
        "urgency": payload.get("urgency", "Normal"),
        "neg_mode": payload.get("neg_mode", "auto"),
        "location": payload.get("location", "Unknown"),
        "notes": payload.get("notes", ""),
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Persist in general history and also maybe in a dedicated table if needed
    await Database.add_history_async(ROLE_OFFER_USER_ID, {"type": "ROLE_OFFER", **record})
    return record


async def list_role_offers(role: str | None = None, user_id: str | None = None):
    entries = await Database.get_history_async(ROLE_OFFER_USER_ID)
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

