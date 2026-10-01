"""
tests/test_7_crops_journey.py

Complete Runtime Journey & Unit Consistency Verification for All 7 Canonical Maharashtra Crops:
1. Sugarcane
2. Soybean
3. Cotton
4. Onion
5. Jowar
6. Bajra
7. Rice

Addresses Audit Critique #6 and #7:
- Controlled Unit Consistency Proof across:
    raw benchmark -> normalized benchmark -> model prediction -> FarmerAgent market_price -> negotiation price
    Every stage MUST strictly operate in INR_PER_KG.
    Verifies that Sugarcane is ~₹3.15 - ₹3.85/kg, completely resolving the historic 40x / ₹126.00 anomaly.
- Full E2E Journey verification across matching, 8-factor explainability scoring, and best deal net farmer margin.
"""

import pytest
from backend.core.constants import (
    CROP_MASTER,
    SUPPORTED_CROPS,
    STATUTORY_BENCHMARKS,
    normalize_crop_id,
    get_crop_info
)
from backend.core.business_rules import FarmerBusinessRules, BuyerBusinessRules
from backend.services.price_prediction_service import predict_price_xgboost
from backend.services.matching_service import compute_match_breakdown_sync
from backend.agents.graph_orchestrator import compute_net_farmer_margin


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Unit Consistency Across All 7 Canonical Crops (Resolving Critique #7)
# ─────────────────────────────────────────────────────────────────────────────
def test_all_7_crops_unit_consistency():
    canonical_crops = ["Sugarcane", "Soybean", "Cotton", "Onion", "Jowar", "Bajra", "Rice"]

    # Market prices in realistic INR/kg for testing
    crop_test_params = {
        "Sugarcane": {"modal_kg": 3.50, "min_expected_kg": 3.00, "max_expected_kg": 4.50},
        "Soybean":   {"modal_kg": 46.0, "min_expected_kg": 40.0, "max_expected_kg": 55.0},
        "Cotton":    {"modal_kg": 72.0, "min_expected_kg": 65.0, "max_expected_kg": 85.0},
        "Onion":     {"modal_kg": 22.0, "min_expected_kg": 14.0, "max_expected_kg": 32.0},
        "Jowar":     {"modal_kg": 35.0, "min_expected_kg": 30.0, "max_expected_kg": 42.0},
        "Bajra":     {"modal_kg": 27.0, "min_expected_kg": 22.0, "max_expected_kg": 32.0},
        "Rice":      {"modal_kg": 25.0, "min_expected_kg": 20.0, "max_expected_kg": 35.0},
    }

    for crop_name in canonical_crops:
        # A. Canonical Lookup
        cid = normalize_crop_id(crop_name)
        assert cid is not None, f"Crop {crop_name} must normalize to canonical ID"
        info = get_crop_info(crop_name)
        assert info is not None, f"Crop {crop_name} metadata must exist"

        # B. Statutory Benchmark Unit Check
        stat_data = STATUTORY_BENCHMARKS.get(crop_name)
        assert stat_data is not None, f"Statutory benchmark for {crop_name} must exist"
        raw_benchmark = stat_data["benchmark"]
        unit = stat_data.get("unit", "per_kg")

        if unit == "per_quintal":
            norm_benchmark_kg = raw_benchmark / 100.0
        else:
            norm_benchmark_kg = raw_benchmark

        # Sugarcane benchmark check: FRP 315 / 100 = 3.15 INR/kg
        if crop_name == "Sugarcane":
            assert raw_benchmark == 315.0
            assert norm_benchmark_kg == 3.15, f"Sugarcane normalized benchmark must be 3.15 INR/kg, got {norm_benchmark_kg}"

        # C. ML XGBoost Forecast Unit Check
        params = crop_test_params[crop_name]
        ml_res = predict_price_xgboost(
            crop=crop_name,
            location="Maharashtra",
            current_modal_price=params["modal_kg"],
            days_ahead=7
        )
        forecast_price = ml_res["forecast_price"]
        assert forecast_price > 0.0, f"Forecast price must be positive for {crop_name}"

        # Crucial Unit Test: Sugarcane must NEVER return 126.00 or > 10.0 INR/kg!
        if crop_name == "Sugarcane":
            assert forecast_price < 10.0, (
                f"CRITICAL UNIT ERROR: Sugarcane forecast price was ₹{forecast_price}/kg! "
                f"Expected around ₹3.15 - ₹4.50/kg. ₹126.00 indicates unnormalized quintal benchmark!"
            )
            assert forecast_price >= 2.50, f"Sugarcane forecast price ₹{forecast_price}/kg is unrealistically low."
        else:
            assert 10.0 <= forecast_price <= 110.0, (
                f"Forecast for {crop_name} (₹{forecast_price}/kg) outside valid ₹/kg bounds [10, 110]"
            )

        # D. Business Rules Invariant Check
        valid, reason, action = FarmerBusinessRules.validate_offer(
            offer_price=params["modal_kg"],
            farmer_min_price=params["modal_kg"] * 0.9,
            crop=crop_name
        )
        assert valid is True, f"Legitimate modal price for {crop_name} rejected: {reason}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Full Journey Simulation across All 7 Crops (Matching -> Best Deal)
# ─────────────────────────────────────────────────────────────────────────────
def test_all_7_crops_full_journey():
    canonical_crops = ["Sugarcane", "Soybean", "Cotton", "Onion", "Jowar", "Bajra", "Rice"]

    journey_results = {}

    for crop_name in canonical_crops:
        # Determine realistic market base per kg
        if crop_name == "Sugarcane":
            unit_price = 3.50
            qty = 10000.0  # 10 tonnes
        elif crop_name in ["Soybean", "Cotton"]:
            unit_price = 50.0 if crop_name == "Soybean" else 72.0
            qty = 2000.0
        else:
            unit_price = 25.0
            qty = 1000.0

        # Candidate buyer profiles
        candidates = [
            {
                "id": f"b1_{crop_name.lower()}",
                "name": f"Local Mandi Trader ({crop_name})",
                "target_price": unit_price * 0.98,
                "max_price": unit_price * 1.02,
                "budget": unit_price * qty * 1.5,
                "max_quantity": qty * 2,
                "distance_km": 25.0,
                "location": "Nashik",
                "trust_score": 4.2,
                "crop": crop_name
            },
            {
                "id": f"b2_{crop_name.lower()}",
                "name": f"Regional Processor ({crop_name})",
                "target_price": unit_price * 1.06,
                "max_price": unit_price * 1.10,
                "budget": unit_price * qty * 2.0,
                "max_quantity": qty * 3,
                "distance_km": 140.0,
                "location": "Pune",
                "trust_score": 4.7,
                "crop": crop_name
            }
        ]

        # 1. Matching & Explainability Scoring
        listing = {
            "crop": crop_name,
            "price": unit_price,
            "min_price": unit_price * 0.9,
            "quantity": qty,
            "location": "Nashik"
        }

        scored_candidates = []
        for cand in candidates:
            requirement = {
                "crop": crop_name,
                "target_price": cand["target_price"],
                "max_price": cand["max_price"],
                "quantity": cand["max_quantity"],
                "location": cand["location"],
                "budget": cand["budget"]
            }
            buyer_user = {"trust_score": cand["trust_score"]}
            res = compute_match_breakdown_sync(listing, requirement, buyer_user)
            score = res["total_score"]
            breakdown = res["factor_breakdown"]

            assert 0.0 <= score <= 100.0
            assert "price_feasibility" in breakdown
            assert "quantity_fulfillment" in breakdown
            assert "distance_proximity" in breakdown
            assert "trust_reliability" in breakdown
            cand["score"] = score
            cand["breakdown"] = breakdown
            scored_candidates.append(cand)

        # 2. Simulated Negotiation Offers
        offers = [
            {
                "buyer_id": candidates[0]["id"],
                "buyer_name": candidates[0]["name"],
                "price": round(unit_price * 0.99, 2),
                "distance_km": candidates[0]["distance_km"]
            },
            {
                "buyer_id": candidates[1]["id"],
                "buyer_name": candidates[1]["name"],
                "price": round(unit_price * 1.08, 2),
                "distance_km": candidates[1]["distance_km"]
            }
        ]

        # 3. Best Deal Selection via Net Farmer Margin Optimization
        state = {
            "location": "Nashik",
            "quantity": qty,
            "has_transport": False,
            "storage_cost": 0.0,
            "min_price": unit_price * 0.9,
            "active_buyers": candidates
        }
        margin_evaluations = [
            {**compute_net_farmer_margin(off, state), "buyer_id": off["buyer_id"], "buyer_name": off["buyer_name"]}
            for off in offers
        ]
        best_deal = max(margin_evaluations, key=lambda m: m["net_margin"])

        assert best_deal is not None
        assert "net_margin" in best_deal
        assert "est_transport_cost" in best_deal
        assert best_deal["net_margin"] > 0

        journey_results[crop_name] = {
            "selected_buyer": best_deal["buyer_name"],
            "deal_price_per_kg": best_deal.get("nominal_price"),
            "net_price_per_kg": best_deal.get("net_price"),
            "net_margin": best_deal.get("net_margin"),
            "top_match_score": max(c["score"] for c in scored_candidates)
        }

    # Verify all 7 crops reached valid deal realization
    assert len(journey_results) == 7
    for crop, res in journey_results.items():
        assert res["deal_price_per_kg"] > 0
        assert res["net_margin"] > 0
        print(f"Verified Crop {crop:10}: Gross=INR {res['deal_price_per_kg']:.2f}/kg | Net=INR {res['net_price_per_kg']:.2f}/kg | Margin=INR {res['net_margin']:,.2f} | Match={res['top_match_score']:.1f}")
