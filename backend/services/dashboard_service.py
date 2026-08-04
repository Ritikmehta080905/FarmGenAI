"""
backend/services/dashboard_service.py

Dashboard Statistics Service — FR-13: Analytics & Dashboard

Aggregates real-time platform metrics for admin and user dashboards.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from database.db import Database

logger = logging.getLogger("DashboardService")


def get_platform_summary() -> Dict[str, Any]:
    """
    Aggregate-level platform statistics (admin view).
    """
    all_negs = list(Database.negotiations.values())
    all_users = list(Database.users.values())

    total_negs = len(all_negs)
    deals = [n for n in all_negs if n.get("status") == "DEAL"]
    storage_escalations = [n for n in all_negs if "STORAGE" in str(n.get("status", ""))]
    processing_escalations = [n for n in all_negs if "PROCESSING" in str(n.get("status", ""))]
    compost_escalations = [n for n in all_negs if "COMPOST" in str(n.get("status", ""))]
    failed = [n for n in all_negs if n.get("status") in ("FAILED", "REJECT", "CANCELLED")]

    # Price analytics
    prices = [float(n.get("final_price", 0)) for n in deals if n.get("final_price")]
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
    max_price = round(max(prices), 2) if prices else 0.0
    min_deal_price = round(min(prices), 2) if prices else 0.0

    # Quantity
    quantities = [float(n.get("quantity", 0)) for n in deals if n.get("quantity")]
    total_volume_kg = round(sum(quantities), 2)

    # GMV (Gross Merchandise Value)
    gmv_values = [
        float(n.get("final_price", 0)) * float(n.get("quantity", 0))
        for n in deals
        if n.get("final_price") and n.get("quantity")
    ]
    total_gmv = round(sum(gmv_values), 2)

    # User metrics
    total_users = len(all_users)
    farmers = [u for u in all_users if u.get("role") == "farmer"]
    buyers = [u for u in all_users if u.get("role") == "buyer"]
    verified = [u for u in all_users if u.get("verification_status") == "VERIFIED"]

    # Crop distribution
    crop_counts: Dict[str, int] = {}
    for n in all_negs:
        crop = n.get("crop", "Unknown")
        crop_counts[crop] = crop_counts.get(crop, 0) + 1

    # Location distribution
    location_counts: Dict[str, int] = {}
    for n in all_negs:
        loc = n.get("location", "Unknown")
        location_counts[loc] = location_counts.get(loc, 0) + 1

    return {
        "negotiations": {
            "total": total_negs,
            "deals": len(deals),
            "storage_escalations": len(storage_escalations),
            "processing_escalations": len(processing_escalations),
            "compost_escalations": len(compost_escalations),
            "failed": len(failed),
            "success_rate_pct": round((len(deals) / total_negs) * 100, 1) if total_negs else 0.0,
        },
        "pricing": {
            "average_deal_price": avg_price,
            "max_deal_price": max_price,
            "min_deal_price": min_deal_price,
        },
        "volume": {
            "total_traded_kg": total_volume_kg,
            "total_gmv": total_gmv,
        },
        "users": {
            "total": total_users,
            "farmers": len(farmers),
            "buyers": len(buyers),
            "verified": len(verified),
        },
        "distributions": {
            "crops": dict(sorted(crop_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "locations": dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_farmer_dashboard(user_id: str) -> Dict[str, Any]:
    """Per-farmer dashboard view."""
    all_negs = list(Database.negotiations.values())
    my_negs = [n for n in all_negs if n.get("user_id") == user_id]

    deals = [n for n in my_negs if n.get("status") == "DEAL"]
    prices = [float(n.get("final_price", 0)) for n in deals if n.get("final_price")]
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    # Earnings
    earnings_values = [
        float(n.get("final_price", 0)) * float(n.get("quantity", 0))
        for n in deals if n.get("final_price") and n.get("quantity")
    ]
    total_earnings = round(sum(earnings_values), 2)

    history = Database.get_history(user_id)
    recent_activity = history[:5]

    user = Database.get_user(user_id) or {}

    return {
        "user": {
            "user_id": user_id,
            "name": user.get("name"),
            "trust_score": user.get("trust_score", 4.0),
            "verification_status": user.get("verification_status", "PENDING"),
        },
        "negotiations": {
            "total": len(my_negs),
            "successful": len(deals),
            "pending": len([n for n in my_negs if n.get("status") in ("RUNNING", "ACTIVE")]),
            "failed": len([n for n in my_negs if n.get("status") in ("FAILED", "REJECT")]),
        },
        "earnings": {
            "total": total_earnings,
            "average_price": avg_price,
        },
        "recent_activity": recent_activity,
    }


def get_buyer_dashboard(user_id: str) -> Dict[str, Any]:
    """Per-buyer dashboard view."""
    history = Database.get_history(user_id)
    deal_history = [h for h in history if h.get("status") == "DEAL"]

    purchased_kg = sum(float(h.get("quantity", 0)) for h in deal_history)
    spent = sum(
        float(h.get("final_price", 0)) * float(h.get("quantity", 0))
        for h in deal_history
        if h.get("final_price") and h.get("quantity")
    )

    user = Database.get_user(user_id) or {}

    return {
        "user": {
            "user_id": user_id,
            "name": user.get("name"),
            "trust_score": user.get("trust_score", 4.0),
        },
        "purchases": {
            "total_deals": len(deal_history),
            "total_kg_purchased": round(purchased_kg, 2),
            "total_spent": round(spent, 2),
        },
        "recent_activity": history[:5],
    }
