"""
backend/services/transporter_marketplace_service.py

Large-Scale Autonomous Transporter Marketplace & Candidate Intelligence Engine.
Separates Transport Providers (Counterparties) from Vehicles (Assets).
Implements:
1. Multi-tier Transporter Marketplace Pool Generation (10, 50, 100, 200, 500+ providers).
2. Hard Constraint Provider & Vehicle Filtering (Capacity, Refrigeration, Deadline).
3. Transporter vs. Vehicle Aggregation (1 provider -> 1 best vehicle offer).
4. Strictly Normalized Multi-Factor Matching Score in [0, 100].
5. Adaptive Candidate Expansion across sequential shortlist windows.
6. Pool Exhaustion Protocol (NO_TRANSPORT_AVAILABLE).
7. Post-Deal Economic Settlement Feasibility Audit (Farmer Floor Protection).
"""

import logging
import json
import os
import random
from typing import List, Dict, Any, Optional, Tuple
from backend.services.routing_service import calculate_transport_route
from backend.services.transport_cost_service import calculate_transportation_cost

logger = logging.getLogger("TransporterMarketplaceService")

MAHARASHTRA_DISTRICTS = [
    "Pune", "Nashik", "Ahmednagar", "Nagpur", "Solapur", 
    "Aurangabad", "Kolhapur", "Latur", "Jalgaon", "Amravati", 
    "Mumbai", "Satara", "Sangli", "Nanded", "Dhule"
]

VEHICLE_CATALOG = [
    {"type": "Cargo Three-Wheeler", "capacity": 600.0, "kmpl": 16.0, "reefer": False, "rate": 12.0},
    {"type": "Mini Truck", "capacity": 1500.0, "kmpl": 12.0, "reefer": False, "rate": 18.0},
    {"type": "LCV", "capacity": 2500.0, "kmpl": 10.0, "reefer": False, "rate": 22.0},
    {"type": "Medium Truck", "capacity": 5000.0, "kmpl": 8.0, "reefer": False, "rate": 32.0},
    {"type": "Refrigerated Truck", "capacity": 4000.0, "kmpl": 6.5, "reefer": True, "rate": 45.0},
    {"type": "Cold Chain Reefer", "capacity": 8000.0, "kmpl": 5.5, "reefer": True, "rate": 55.0},
    {"type": "Heavy Truck", "capacity": 12000.0, "kmpl": 5.0, "reefer": False, "rate": 50.0},
    {"type": "Tractor + Trailer", "capacity": 7000.0, "kmpl": 7.0, "reefer": False, "rate": 25.0}
]


def load_seed_transporters() -> List[Dict[str, Any]]:
    """Loads base seed transporter records from transporters.json."""
    seed_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "transporters.json")
    if os.path.exists(seed_path):
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read transporters.json: {e}")
    return []


def generate_transporter_marketplace(pool_size: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates an active, multi-counterparty marketplace of Transport Providers.
    Each Transport Provider owns a fleet of 1 to 4 distinct vehicles.
    """
    rng = random.Random(seed)
    seed_data = load_seed_transporters()
    providers: List[Dict[str, Any]] = []

    for i in range(pool_size):
        provider_id = f"TR-PROV-{i+1:04d}"
        if i < len(seed_data):
            base = seed_data[i]
            prov_name = base.get("provider_name", f"Logistics Provider {i+1}")
            loc = base.get("current_location", rng.choice(MAHARASHTRA_DISTRICTS))
            rating = float(base.get("rating", round(rng.uniform(3.5, 4.9), 1)))
        else:
            dist = rng.choice(MAHARASHTRA_DISTRICTS)
            prov_name = f"{dist} Agro-Express Carrier #{i+1}"
            loc = dist
            rating = round(rng.uniform(3.5, 4.9), 1)

        reliability = round(min(1.0, max(0.6, rating / 5.0 - rng.uniform(0.0, 0.05))), 2)
        total_trips = rng.randint(45, 1200)
        cancellation_rate = round(rng.uniform(0.01, 0.08), 3)

        # Generate provider fleet (1 to 4 vehicles)
        fleet_size = rng.randint(1, 4)
        fleet = []
        for v_idx in range(fleet_size):
            spec = rng.choice(VEHICLE_CATALOG)
            vehicle_id = f"{provider_id}-V{v_idx+1}"
            fleet.append({
                "vehicle_id": vehicle_id,
                "transporter_id": provider_id,
                "provider_name": prov_name,
                "vehicle_type": spec["type"],
                "vehicle_name": f"{prov_name} ({spec['type']})",
                "capacity_kg": spec["capacity"],
                "fuel_type": "Diesel",
                "fuel_efficiency_kmpl": spec["kmpl"],
                "current_location": loc,
                "refrigerated": spec["reefer"],
                "rate_per_km": spec["rate"],
                "status": "AVAILABLE" if rng.random() > 0.10 else "IN_TRANSIT",
                "rating": rating
            })

        providers.append({
            "provider_id": provider_id,
            "provider_name": prov_name,
            "current_location": loc,
            "rating": rating,
            "reliability_score": reliability,
            "total_trips": total_trips,
            "cancellation_rate": cancellation_rate,
            "fleet_size": len(fleet),
            "fleet": fleet
        })

    return providers


def filter_and_rank_transporter_candidates(
    providers: List[Dict[str, Any]],
    transport_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Executes hard-constraint filtering and strictly normalized multi-factor ranking.
    Separates Transporter Provider from Vehicle:
    Each eligible provider is evaluated across its fleet, and its single best vehicle
    is selected to prevent one fleet from monopolizing candidate slots.
    """
    req_qty = float(transport_request.get("quantity_kg", 1000.0))
    req_refrig = bool(transport_request.get("refrigerated_required", False))
    pickup_loc = transport_request.get("pickup_location", "Ahmednagar")
    delivery_loc = transport_request.get("delivery_location", "Pune")
    deadline_h = float(transport_request.get("delivery_deadline_hours", 24.0))
    shelf_life_h = float(transport_request.get("shelf_life_hours", 48.0))
    urgency = transport_request.get("urgency", "NORMAL").upper()

    total_pool = len(providers)
    eligible_candidates: List[Dict[str, Any]] = []
    rejected_reasons: Dict[str, int] = {
        "NO_AVAILABLE_VEHICLES": 0,
        "INSUFFICIENT_CAPACITY": 0,
        "REFRIGERATION_MISMATCH": 0,
        "DEADLINE_EXCEEDED": 0,
        "DISTANCE_EXCEEDED": 0
    }

    for p in providers:
        fleet = p.get("fleet", [])
        valid_fleet_for_req = []

        for v in fleet:
            if v.get("status") != "AVAILABLE":
                continue
            if v.get("capacity_kg", 0) < req_qty:
                continue
            if req_refrig and not v.get("refrigerated", False):
                continue
            valid_fleet_for_req.append(v)

        if not valid_fleet_for_req:
            # Determine dominant rejection reason for this provider
            has_avail = any(v.get("status") == "AVAILABLE" for v in fleet)
            if not has_avail:
                rejected_reasons["NO_AVAILABLE_VEHICLES"] += 1
            elif req_refrig and not any(v.get("refrigerated") for v in fleet):
                rejected_reasons["REFRIGERATION_MISMATCH"] += 1
            else:
                rejected_reasons["INSUFFICIENT_CAPACITY"] += 1
            continue

        # Sort vehicles in fleet by least capacity excess (tightest fit)
        valid_fleet_for_req.sort(key=lambda x: x["capacity_kg"] - req_qty)
        best_vehicle = valid_fleet_for_req[0]

        # Calculate routing distance and duration
        route = calculate_transport_route(
            pickup_location=pickup_loc,
            delivery_location=delivery_loc,
            vehicle_current_location=p["current_location"]
        )
        total_dist = route.get("total_operational_distance_km", 50.0)
        duration_h = route.get("total_travel_duration_hours", 2.0)

        # Hard constraint: Distance <= 600km
        if total_dist > 600.0:
            rejected_reasons["DISTANCE_EXCEEDED"] += 1
            continue

        # Hard constraint: Duration <= Deadline
        if duration_h > deadline_h:
            rejected_reasons["DEADLINE_EXCEEDED"] += 1
            continue

        # --- Normalized Multi-Factor Scoring in [0.0, 1.0] ---
        # 1. Distance proximity (0 to 1, max score at 0 distance)
        s_dist = max(0.0, 1.0 - (total_dist / 600.0))

        # 2. Capacity utilization (0 to 1, peak score when capacity closely matches requested payload)
        cap_excess_pct = (best_vehicle["capacity_kg"] - req_qty) / max(best_vehicle["capacity_kg"], 1.0)
        s_cap = max(0.0, 1.0 - cap_excess_pct)

        # 3. Provider Reliability & Rating (0 to 1)
        s_rel = (p.get("rating", 4.0) / 5.0) * (1.0 - p.get("cancellation_rate", 0.05))

        # 4. Delivery Deadline Buffer (0 to 1)
        s_deadline = max(0.0, 1.0 - (duration_h / max(deadline_h, 1.0)))

        # 5. Refrigeration Compliance (0 to 1)
        s_refrig = 1.0 if (req_refrig and best_vehicle["refrigerated"]) else (1.0 if not req_refrig else 0.0)

        # 6. Tariff Feasibility (0 to 1)
        s_rate = max(0.0, 1.0 - (best_vehicle.get("rate_per_km", 20.0) - 12.0) / 45.0)

        # Weighted Composite Score strictly in [0.0, 100.0]
        # Weights: Dist(25%), Cap(20%), Rel(20%), Deadline(15%), Refrig(10%), Rate(10%)
        composite_score = round(100.0 * (
            0.25 * s_dist +
            0.20 * s_cap +
            0.20 * s_rel +
            0.15 * s_deadline +
            0.10 * s_refrig +
            0.10 * s_rate
        ), 2)

        explainability = {
            "distance_score_pct": round(s_dist * 25.0, 2),
            "capacity_score_pct": round(s_cap * 20.0, 2),
            "reliability_score_pct": round(s_rel * 20.0, 2),
            "deadline_score_pct": round(s_deadline * 15.0, 2),
            "refrigeration_score_pct": round(s_refrig * 10.0, 2),
            "rate_score_pct": round(s_rate * 10.0, 2),
            "total_composite_score": composite_score
        }

        eligible_candidates.append({
            "provider_id": p["provider_id"],
            "provider_name": p["provider_name"],
            "location": p["current_location"],
            "rating": p["rating"],
            "reliability_score": p["reliability_score"],
            "selected_vehicle": best_vehicle,
            "route_distance_km": total_dist,
            "duration_hours": duration_h,
            "match_score": composite_score,
            "explainability": explainability
        })

    # Sort candidates by composite match score descending
    eligible_candidates.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "success": len(eligible_candidates) > 0,
        "total_providers_evaluated": total_pool,
        "eligible_provider_count": len(eligible_candidates),
        "rejected_breakdown": rejected_reasons,
        "ranked_candidates": eligible_candidates,
        "top_candidate": eligible_candidates[0] if eligible_candidates else None
    }


async def adaptive_candidate_expansion_negotiation(
    ranked_candidates: List[Dict[str, Any]],
    transport_request: Dict[str, Any],
    batch_size: int = 5,
    max_batches: int = 4
) -> Dict[str, Any]:
    """
    Executes windowed candidate expansion across ranked providers.
    Batch 1 (1-5) -> If counterparties reject or fail, expands to Batch 2 (6-10), etc.
    If all candidates fail or pool is exhausted, returns NO_TRANSPORT_AVAILABLE.
    """
    if not ranked_candidates:
        return {
            "status": "NO_TRANSPORT_AVAILABLE",
            "reason": "CANDIDATE_POOL_EXHAUSTED",
            "rounds_attempted": 0,
            "total_contacted": 0,
            "final_deal": None,
            "logs": ["❌ Initial candidate pool is empty. No transport providers available."]
        }

    logs = []
    total_contacted = 0
    buyer_offer = transport_request.get("buyer_offer")

    for batch_idx in range(max_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(ranked_candidates))

        if start_idx >= len(ranked_candidates):
            logs.append(f"ℹ️ Total candidate pool exhausted after {total_contacted} providers evaluated.")
            break

        current_window = ranked_candidates[start_idx:end_idx]
        logs.append(
            f"🔄 [Adaptive Expansion] Batch {batch_idx+1}: Contacting candidates {start_idx+1} to {end_idx} "
            f"({len(current_window)} providers)."
        )

        for candidate in current_window:
            total_contacted += 1
            vehicle = candidate["selected_vehicle"]
            dist = candidate["route_distance_km"]
            duration = candidate["duration_hours"]

            # Calculate deterministic operating cost and transport floor price
            cost_res = await calculate_transportation_cost(
                vehicle=vehicle,
                distance_km=dist,
                estimated_duration_hours=duration,
                deadhead_km=0.0
            )

            transport_floor_price = (
                candidate.get("floor_price_override") or
                vehicle.get("floor_price_override") or
                cost_res["minimum_acceptable_price"]
            )
            initial_quote = max(cost_res["initial_quote"], transport_floor_price * 1.15)

            # Negotiation logic:
            # If buyer_offer is present:
            # If buyer_offer >= transport_floor_price -> ACCEPT
            # Else -> COUNTER / REJECT
            if buyer_offer and buyer_offer >= transport_floor_price:
                logs.append(
                    f"✅ [Deal Reached] Provider {candidate['provider_name']} accepted offer ₹{buyer_offer:,.2f} "
                    f"(Floor: ₹{transport_floor_price:,.2f})."
                )
                return {
                    "status": "DEAL_CONFIRMED",
                    "winning_provider": candidate,
                    "agreed_freight": buyer_offer,
                    "transport_floor_price": transport_floor_price,
                    "cost_breakdown": cost_res,
                    "rounds_attempted": batch_idx + 1,
                    "total_contacted": total_contacted,
                    "logs": logs
                }
            elif not buyer_offer:
                # Direct booking from initial quote
                logs.append(
                    f"✅ [Quote Accepted] Provider {candidate['provider_name']} quoted ₹{initial_quote:,.2f}."
                )
                return {
                    "status": "DEAL_CONFIRMED",
                    "winning_provider": candidate,
                    "agreed_freight": initial_quote,
                    "transport_floor_price": transport_floor_price,
                    "cost_breakdown": cost_res,
                    "rounds_attempted": batch_idx + 1,
                    "total_contacted": total_contacted,
                    "logs": logs
                }
            else:
                logs.append(
                    f"⚠️ Provider {candidate['provider_name']} rejected offer ₹{buyer_offer:,.2f} "
                    f"(Below floor ₹{transport_floor_price:,.2f}). Continuing..."
                )

    # If loop concludes without deal
    logs.append(f"❌ [Exhausted] All {total_contacted} candidate providers rejected the proposed commercial terms.")
    return {
        "status": "NO_TRANSPORT_AVAILABLE",
        "reason": "CANDIDATE_POOL_EXHAUSTED",
        "rounds_attempted": max_batches,
        "total_contacted": total_contacted,
        "final_deal": None,
        "logs": logs
    }


def audit_economic_settlement(
    gross_revenue: float,
    actual_carrier_freight: float,
    actual_storage_cost: float,
    quantity_kg: float,
    farmer_product_floor_price: float
) -> Dict[str, Any]:
    """
    Strict Post-Deal Economic Settlement Feasibility Audit.
    Protects the farmer from margin dilution where carrier freight breaks produce profitability.
    """
    qty = max(quantity_kg, 1.0)
    net_margin = gross_revenue - actual_carrier_freight - actual_storage_cost
    net_realization_per_kg = round(net_margin / qty, 2)
    is_profitable = net_realization_per_kg >= farmer_product_floor_price

    if is_profitable:
        status = "FEASIBLE_PROFITABLE"
        action = "CONFIRM_BOOKING"
        msg = (
            f"Net farmer realization of ₹{net_realization_per_kg}/kg exceeds product floor "
            f"₹{farmer_product_floor_price}/kg. Booking approved."
        )
    else:
        status = "SETTLEMENT_REJECTED_FLOOR_VIOLATED"
        action = "REJECT_BOOKING"
        dilution = round(farmer_product_floor_price - net_realization_per_kg, 2)
        msg = (
            f"Actual carrier freight of ₹{actual_carrier_freight:,.2f} dilutes net realization to "
            f"₹{net_realization_per_kg}/kg, which is ₹{dilution}/kg below farmer floor "
            f"₹{farmer_product_floor_price}/kg. Booking REJECTED."
        )

    return {
        "status": status,
        "action": action,
        "gross_revenue": round(gross_revenue, 2),
        "actual_carrier_freight": round(actual_carrier_freight, 2),
        "actual_storage_cost": round(actual_storage_cost, 2),
        "net_margin": round(net_margin, 2),
        "final_net_realization_per_kg": net_realization_per_kg,
        "farmer_product_floor_price": farmer_product_floor_price,
        "is_profitable_above_floor": is_profitable,
        "audit_message": msg
    }
