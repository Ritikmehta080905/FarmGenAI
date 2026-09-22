import logging
import asyncio
from typing import Dict, Any, List
from backend.services.vehicle_service import filter_suitable_vehicles
from backend.services.recommendation_service import recommend_vehicles_for_request
from backend.services.transport_cost_service import calculate_transportation_cost
from backend.services.routing_service import calculate_transport_route
from llm.llm_client import LLMClient
from backend.agents.transport_agent.prompts import TRANSPORT_NEGOTIATION_PROMPT

logger = logging.getLogger("AutoNegotiationService")
llm_client = LLMClient()

async def run_parallel_negotiation(transport_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates automated agent-to-agent negotiation for the top recommended vehicles.
    """
    quantity_kg = float(transport_request.get("quantity_kg", 1000.0))
    refrigerated_required = bool(transport_request.get("refrigerated_required", False))
    pickup_location = transport_request.get("pickup_location", "Ahmednagar")
    delivery_location = transport_request.get("delivery_location", "Pune")
    crop = transport_request.get("crop", "Produce")

    # 1. Filter and Recommend
    filter_res = await filter_suitable_vehicles(
        quantity_kg=quantity_kg,
        refrigerated_required=refrigerated_required
    )
    
    if not filter_res.get("success"):
        return {
            "success": False,
            "message": "No vehicles meet the basic hard constraints.",
            "candidates": []
        }

    candidates = filter_res.get("candidates", [])
    scored_candidates = recommend_vehicles_for_request(candidates, transport_request)
    
    # Take top 3 for parallel negotiation
    top_candidates = scored_candidates[:3]
    
    negotiation_tasks = []
    for vehicle in top_candidates:
        negotiation_tasks.append(simulate_agent_negotiation(vehicle, pickup_location, delivery_location, crop, transport_request.get("buyer_offer")))

    results = await asyncio.gather(*negotiation_tasks)
    
    # 2. Find the winner (Successful deal with the lowest agreed price)
    successful_deals = [r for r in results if r["status"] == "ACCEPTED"]
    winner = None
    if successful_deals:
        # Sort by agreed price ascending, then by recommendation score descending
        successful_deals.sort(key=lambda x: (x["agreed_price"], -x["vehicle"]["recommendation_score"]))
        winner = successful_deals[0]

    return {
        "success": True,
        "winner": winner,
        "all_negotiations": results
    }


async def simulate_agent_negotiation(vehicle: Dict[str, Any], pickup: str, delivery: str, crop: str, buyer_offer: float = None) -> Dict[str, Any]:
    """Simulates a rapid 3-round negotiation between Stakeholder Agent and Transport Agent."""
    
    # 1. Calculate Route & Costs (Transport Agent's perspective)
    route_info = calculate_transport_route(pickup, delivery, vehicle.get("current_location", pickup))
    distance_km = route_info["distance_km"]
    
    is_perishable = crop.lower() in {"tomato", "banana", "strawberry", "grape", "mango", "milk"}
    cost_result = await calculate_transportation_cost(
        vehicle=vehicle,
        distance_km=distance_km,
        estimated_duration_hours=route_info["estimated_duration_hours"],
        deadhead_km=route_info["deadhead_km"],
        is_perishable=is_perishable
    )

    floor_price = cost_result["minimum_acceptable_price"]
    initial_quote = cost_result["initial_quote"]
    target_price = cost_result["target_price"]
    total_cost = cost_result["total_operating_cost"]

    # 2. Stakeholder Agent's perspective (wants a deal, but has a budget)
    # Assume market average is total_cost + 20%. Stakeholder wants it for total_cost + 10%
    market_average = total_cost * 1.20
    stakeholder_budget = total_cost * 1.10
    
    transcript = []
    current_round = 1
    max_rounds = 3
    
    # Use user's manual floor price (budget) if provided, otherwise start aggressive
    current_stakeholder_offer = buyer_offer if buyer_offer else round(total_cost * 1.05)
    agent_counter = initial_quote
    status = "IN_NEGOTIATION"
    agreed_price = None

    while current_round <= max_rounds:
        # Evaluate Stakeholder's offer
        if current_stakeholder_offer >= floor_price:
            status = "ACCEPTED"
            agreed_price = current_stakeholder_offer
            agent_counter = current_stakeholder_offer
            v_name = vehicle.get('vehicle_name', 'Truck')
            v_fuel = vehicle.get('fuel_type', 'Diesel')
            fuel_cost = round(cost_result['cost_breakdown']['fuel_cost'])
            toll_cost = round(cost_result['cost_breakdown']['toll_cost'])
            explanation = f"Offer of ₹{current_stakeholder_offer} accepted for my {v_name} ({v_fuel}). This covers my ₹{fuel_cost} fuel overhead plus ₹{toll_cost} in tolls for the {distance_km}km trip."
        else:
            if current_round == max_rounds:
                status = "REJECTED"
                agent_counter = None
                explanation = f"Offer of ₹{current_stakeholder_offer} is rejected. My {vehicle.get('fuel_type', 'Diesel')} alone for this {distance_km}km trip costs ₹{round(cost_result['cost_breakdown']['fuel_cost'])}, so I cannot accept anything below ₹{floor_price}."
            else:
                status = "COUNTERED"
                gap = target_price - floor_price
                reduction_factor = (current_round / max_rounds) * 0.7
                agent_counter = round(max(floor_price, target_price - (gap * reduction_factor)), 2)
                explanation = f"Your offer of ₹{current_stakeholder_offer} is too low for a {vehicle.get('vehicle_type', 'truck')} on this {distance_km}km route. Factoring in fuel and maintenance, my counter-offer is ₹{agent_counter}."

        # Optionally generate a quick LLM explanation for realism
        llm_prompt = TRANSPORT_NEGOTIATION_PROMPT.format(
            crop=crop,
            quantity_kg=vehicle.get("capacity_kg", 1000),
            pickup_location=pickup,
            delivery_location=delivery,
            distance_km=distance_km,
            estimated_duration_hours=route_info["estimated_duration_hours"],
            vehicle_name=vehicle.get("vehicle_name", "Vehicle"),
            vehicle_type=vehicle.get("vehicle_type", "Truck"),
            total_operating_cost=total_cost,
            minimum_acceptable_price=floor_price,
            target_price=target_price,
            buyer_offer=current_stakeholder_offer,
            action=status,
            counter_offer=agent_counter or floor_price
        )

        try:
            llm_response = await asyncio.wait_for(
                asyncio.to_thread(llm_client.generate, llm_prompt, max_tokens=150),
                timeout=1.5
            )
        except Exception as e:
            logger.warning(f"LLM generation failed or timed out: {e}")
            llm_response = None

        final_explanation = llm_response if (llm_response and len(llm_response) > 10) else explanation

        transcript.append({
            "round": current_round,
            "stakeholder_offer": current_stakeholder_offer,
            "transporter_counter": agent_counter,
            "status": status,
            "message": final_explanation
        })

        if status in ["ACCEPTED", "REJECTED"]:
            break
            
        # Stakeholder Agent formulates next offer
        if agent_counter <= stakeholder_budget:
            current_stakeholder_offer = agent_counter # Just accept it in the next round
        else:
            # Compromise halfway between their last offer and the agent's counter
            current_stakeholder_offer = round((current_stakeholder_offer + agent_counter) / 2)
            
        current_round += 1

    return {
        "vehicle": vehicle,
        "status": status,
        "agreed_price": agreed_price,
        "transcript": transcript,
        "route": route_info,
        "pricing_rules": {
            "floor_price": floor_price,
            "market_average": market_average,
            "target_price": target_price,
            "initial_quote": initial_quote
        }
    }
