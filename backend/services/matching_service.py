"""
backend/services/matching_service.py

Matching Engine Service — pairs farmer crop listings with buyer requirements.
Implements FR-5: AI-Powered Matching Engine

Scoring factors (8-factor NRV model):
  1. Base price compatibility   (20%)
  2. Quantity match             (20%)
  3. Distance proximity         (15%)
  4. Trust & Reliability        (15%)
  5. Quality & Grade match      (10%)
  6. Urgency / Spoilage match   (10%)
  7. Transport cost efficiency  (5%)
  8. Storage cost efficiency    (5%)
"""

from backend.repositories.user_repository import UserRepository
import logging
from typing import List, Dict, Optional
from database.db import Database

logger = logging.getLogger("MatchingService")


CITY_DISTANCES_KM: Dict[str, Dict[str, float]] = {
    "Nashik":     {"Nashik": 0, "Pune": 210, "Mumbai": 170, "Nagpur": 450, "Kalyan": 180, "Thane": 165},
    "Pune":       {"Nashik": 210, "Pune": 0, "Mumbai": 150, "Nagpur": 580, "Kalyan": 130, "Thane": 145},
    "Mumbai":     {"Nashik": 170, "Pune": 150, "Mumbai": 0, "Nagpur": 830, "Kalyan": 55, "Thane": 40},
    "Nagpur":     {"Nashik": 450, "Pune": 580, "Mumbai": 830, "Nagpur": 0, "Kalyan": 800, "Thane": 795},
    "Kalyan":     {"Nashik": 180, "Pune": 130, "Mumbai": 55, "Nagpur": 800, "Kalyan": 0, "Thane": 20},
    "Thane":      {"Nashik": 165, "Pune": 145, "Mumbai": 40, "Nagpur": 795, "Kalyan": 20, "Thane": 0},
    "Aurangabad": {"Nashik": 190, "Pune": 230, "Mumbai": 340, "Nagpur": 330, "Kalyan": 300, "Thane": 310},
    "Satara":     {"Nashik": 270, "Pune": 110, "Mumbai": 255, "Nagpur": 690, "Kalyan": 210, "Thane": 225},
    "Ahmednagar": {"Nashik": 120, "Pune": 120, "Mumbai": 275, "Nagpur": 570, "Kalyan": 245, "Thane": 260},
}

MAX_MATCH_DISTANCE_KM = 600.0


async def _get_distance_km(loc_a: str, loc_b: str) -> float:
    """Estimate distance between two locations."""
    if not loc_a or not loc_b:
        return 150.0
    if loc_a == loc_b:
        return 0.0
    a = loc_a.strip()
    b = loc_b.strip()
    dist = CITY_DISTANCES_KM.get(a, {}).get(b)
    if dist is None:
        dist = CITY_DISTANCES_KM.get(b, {}).get(a)
    return dist if dist is not None else 250.0  # default


async def _score_match(listing: Dict, requirement: Dict, buyer_user: Optional[Dict] = None) -> float:
    """
    Compute a 0-100 compatibility score using the 8-factor NRV model.
    """
    score = 0.0

    # 1. Base Price (20 pts)
    min_price = float(listing.get("min_price", 0))
    target_price = float(requirement.get("target_price", 0))
    max_price = float(requirement.get("max_price") or target_price * 1.2)
    if target_price >= min_price:
        score += 20.0
    elif max_price >= min_price:
        ratio = (max_price - min_price) / max(max_price, 1)
        score += max(0, 10 + ratio * 10)

    # 2. Quantity (20 pts)
    avail_qty = float(listing.get("quantity", 0))
    req_qty = float(requirement.get("quantity", 0))
    if req_qty > 0 and avail_qty > 0:
        ratio = min(avail_qty, req_qty) / max(avail_qty, req_qty)
        score += ratio * 20.0

    # 3. Distance (15 pts)
    listing_loc = listing.get("location", "")
    req_loc = requirement.get("location", "")
    dist = await _get_distance_km(listing_loc, req_loc)
    if dist <= MAX_MATCH_DISTANCE_KM:
        score += max(0, 1.0 - dist / MAX_MATCH_DISTANCE_KM) * 15.0

    # 4. Trust (15 pts)
    trust = float((buyer_user or {}).get("trust_score", 3.5))
    score += min(trust / 5.0, 1.0) * 15.0
    
    # 5. Quality/Grade (10 pts)
    list_grade = str(listing.get("grade", "A")).upper()
    req_grade = str(requirement.get("grade", "A")).upper()
    if list_grade == req_grade:
        score += 10.0
    elif list_grade in ["A", "PREMIUM"] and req_grade in ["B", "C", "STANDARD"]:
        score += 8.0 # Downgrading is acceptable
    else:
        score += 4.0 # Upgrading is penalized

    # 6. Urgency / Spoilage (10 pts)
    spoilage = int(listing.get("spoilage_days", listing.get("shelf_life", 14)))
    urgency = str(requirement.get("urgency", "NORMAL")).upper()
    if spoilage <= 3 and urgency == "HIGH":
        score += 10.0
    elif spoilage > 7 and urgency == "LOW":
        score += 10.0
    else:
        score += 6.0
        
    # 7. Transport Cost Efficiency (5 pts)
    # Estimate ₹3 per km per ton
    est_transport_cost = (dist * 3.0 * req_qty) / 1000.0
    budget = float(requirement.get("budget", target_price * req_qty))
    if budget > 0:
        transport_ratio = min(est_transport_cost / budget, 1.0)
        score += (1.0 - transport_ratio) * 5.0
        
    # 8. Storage Cost Efficiency (5 pts)
    if req_qty >= avail_qty:
        score += 5.0  # Immediate full clearance avoids storage
    else:
        score += 2.0  # Partial clearance incurs storage for remainder

    return round(score, 2)


async def match_listing_to_buyers(listing: Dict) -> List[Dict]:
    """
    Find and score all buyer requirements that match a given crop listing.
    Returns ranked list of matches.
    """
    buyers = await Database.list_buyers_async()
    all_requirements = [r for r in buyers if r.get("kind") == "requirement" and r.get("status") == "ACTIVE"]
    
    # Also include simulated buyers / default profiles that might not explicitly have kind="requirement"
    if not all_requirements:
        all_requirements = [b for b in buyers if b.get("kind") != "offer"]

    results = []
    for req in all_requirements:
        # Crop must match (case-insensitive)
        req_crop = (req.get("crop") or "").strip()
        list_crop = (listing.get("crop") or "").strip()
        if not req_crop or (list_crop and req_crop.lower() != list_crop.lower()):
            continue

        buyer_user = await UserRepository.get_by_id(req.get("user_id", "")) or {}
        score = await _score_match(listing, req, buyer_user)
        dist = await _get_distance_km(listing.get("location", ""), req.get("location", ""))
        
        # Calculate derived offer details similar to negotiation_service
        req_qty = float(req.get("quantity") or req.get("max_quantity") or listing.get("quantity", 0))
        offered_qty = min(float(listing.get("quantity", 0)), req_qty)
        min_price = float(listing.get("min_price", 0))
        market_price = float(listing.get("market_price", min_price + 1))
        target_price = float(req.get("target_price") or req.get("max_price") or (min_price * 1.05))

        raw_budget = float(req.get("budget", 0))
        budget = raw_budget if raw_budget > 0 else max(target_price * req_qty * 1.2, min_price * offered_qty * 1.1)
        budget_limited_price = budget / max(offered_qty, 1)
        
        strategy = str(req.get("strategy", "")).lower()
        
        if "restaurant" in strategy or "premium" in strategy:
            opening_bid = min(target_price * 0.95, budget_limited_price)
        else:
            # High-feasibility opening offer: between 88% to 98% of target/market, capped by budget
            base_offer = max(target_price * 0.92, min_price if target_price >= min_price else target_price * 0.88)
            opening_bid = min(target_price, budget_limited_price, max(base_offer, 1.0))
            
        offer_price = round(max(1.0, opening_bid), 2)
        is_viable = offer_price >= min_price

        # Strategic Labelling
        label = "Market Option"
        if is_viable:
            if score > 75: label = "👑 Best Profit"
            elif dist == 0: label = "⚡ Fast Handshake"
            elif "restaurant" in strategy: label = "💎 Premium Match"
            elif score > 50: label = "🎯 Strategic Fit"

        results.append({
            "requirement_id": req.get("requirement_id") or req.get("id"),
            "buyer_id": req.get("user_id") or req.get("id"),
            "buyer_name": req.get("buyer_name") or req.get("name", "Unknown Buyer"),
            "crop": req.get("crop") or list_crop,
            "quantity": req_qty,
            "target_price": target_price,
            "max_price": req.get("max_price"),
            "budget": budget,
            "location": req.get("location", "Market"),
            "strategy": label,
            "offered_price": offer_price,
            "offered_quantity": round(offered_qty, 2),
            "status": "VIABLE" if is_viable else "BELOW_MIN_PRICE",
            "distance_km": dist,
            "compatibility_score": score,
            "score": score, # Alias for compatibility
            "match_grade": "A" if score >= 70 else "B" if score >= 45 else "C",
            "notes": req.get("notes", ""),
        })

    results.sort(key=lambda item: (item["status"] == "VIABLE", item["offered_price"], item["compatibility_score"]), reverse=True)
    return results


async def match_requirement_to_listings(requirement: Dict) -> List[Dict]:
    """
    Find and score all active crop listings that match a buyer requirement.
    """
    from backend.routes.crop_listing_routes import router as _  # ensure module loaded
    listings = await Database.list_produce_async()
    active = [l for l in listings if l.get("status") in ("LISTED", "ACTIVE")]

    results = []
    for listing in active:
        if listing.get("crop", "").lower() != requirement.get("crop", "").lower():
            continue

        buyer_user = await UserRepository.get_by_id(requirement.get("user_id", "")) or {}
        score = await _score_match(listing, requirement, buyer_user)
        dist = await _get_distance_km(listing.get("location", ""), requirement.get("location", ""))

        results.append({
            "listing_id": listing.get("id"),
            "farmer_name": listing.get("farmer_name"),
            "farmer_id": listing.get("user_id"),
            "crop": listing.get("crop"),
            "quantity": listing.get("quantity"),
            "min_price": listing.get("min_price"),
            "location": listing.get("location"),
            "spoilage_days": listing.get("spoilage_days", listing.get("shelf_life", 7)),
            "quality": listing.get("quality", "A"),
            "distance_km": dist,
            "compatibility_score": score,
            "match_grade": "A" if score >= 70 else "B" if score >= 45 else "C",
        })

    results.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return results

