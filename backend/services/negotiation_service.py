from agents.buyer_agent import BuyerAgent
from agents.compost_agent import CompostAgent
from agents.farmer_agent import FarmerAgent
from agents.processor_agent import ProcessorAgent
from agents.transporter_agent import TransporterAgent
from agents.warehouse_agent import WarehouseAgent
from database.db import Database
from backend.services.history_service import add_history
from negotiation_engine.negotiation_manager import NegotiationManager
from datetime import datetime, timezone


DEFAULT_BUYER_PROFILES = [
    {
        "id": "buyer_wholesale_hub",
        "name": "Wholesale Hub",
        "budget": 26000,
        "max_quantity": 1400,
        "target_price": 20,
        "location": "Nashik",
        "strategy": "Bulk purchase for city mandis",
    },
    {
        "id": "buyer_fresh_mart",
        "name": "FreshMart Retail",
        "budget": 21000,
        "max_quantity": 900,
        "target_price": 22,
        "location": "Pune",
        "strategy": "High-quality produce for retail shelves",
    },
    {
        "id": "buyer_food_chain",
        "name": "FoodChain Kitchens",
        "budget": 18500,
        "max_quantity": 700,
        "target_price": 19,
        "location": "Mumbai",
        "strategy": "Stable mid-price demand for kitchens",
    },
    {
        "id": "buyer_export_link",
        "name": "ExportLink Foods",
        "budget": 32000,
        "max_quantity": 1600,
        "target_price": 21,
        "location": "Nagpur",
        "strategy": "Cross-city consolidation buyer",
    },
]


class NegotiationService:
    def __init__(self):
        self.active_negotiations = {}
        self._ensure_default_buyers()

    def _ensure_default_buyers(self):
        if Database.buyers:
            return

        for buyer in DEFAULT_BUYER_PROFILES:
            Database.upsert_buyer(buyer)

    def _build_farmer(self, payload: dict):
        return FarmerAgent(
            name=payload.get("farmer_name", "FarmerAgent"),
            crop=payload["crop"],
            quantity=float(payload["quantity"]),
            min_price=float(payload["min_price"]),
            shelf_life=int(payload.get("shelf_life", 3)),
            location=payload.get("location")
        )

    def _build_buyer(self, buyer_profile: dict):
        return BuyerAgent(
            name=buyer_profile["name"],
            budget=float(buyer_profile["budget"]),
            max_quantity=int(buyer_profile["max_quantity"]),
            target_price=float(buyer_profile["target_price"]),
            location=buyer_profile.get("location", "Market")
        )

    def _build_support_agents(self, payload: dict):
        warehouse = WarehouseAgent(
            name="WarehouseAgent",
            capacity=int(payload.get("warehouse_capacity", 5000)),
            storage_cost_per_kg=float(payload.get("storage_cost_per_kg", 1.8)),
            location=payload.get("location", "Nashik")
        )
        processor = ProcessorAgent(
            name="ProcessorAgent",
            crop_type=payload["crop"],
            processing_capacity=int(payload.get("processor_capacity", payload["quantity"])),
            processing_cost_per_kg=float(payload.get("processing_cost_per_kg", 2.0)),
            target_price=float(payload.get("processor_target_price", payload["min_price"] - 1)),
            max_price=float(payload.get("processor_max_price", payload["min_price"] + 2))
        )
        compost = CompostAgent(name="CompostAgent", base_price=float(payload.get("compost_price", 8)))
        transporter = TransporterAgent(
            name="TransporterAgent",
            vehicle_capacity=int(payload.get("transporter_capacity", payload["quantity"])),
            cost_per_km_per_kg=float(payload.get("transport_cost_per_km_per_kg", 0.03)),
            base_fee=float(payload.get("transport_base_fee", 450))
        )
        return warehouse, processor, compost, transporter

    def _generate_market_offers(self, payload: dict):
        self._ensure_default_buyers()

        quantity = max(float(payload["quantity"]), 1)
        min_price = float(payload["min_price"])
        market_price = float(payload.get("market_price", min_price + 1))
        location = payload.get("location", "Unknown")

        offers = []
        for profile in Database.list_buyers():
            offered_qty = min(quantity, float(profile.get("max_quantity", quantity)))
            if offered_qty <= 0:
                continue

            budget_limited_price = float(profile.get("budget", 0)) / offered_qty
            raw_price = min(float(profile.get("target_price", min_price)), budget_limited_price, market_price + 3)
            offer_price = round(max(1.0, raw_price), 2)
            distance_penalty = 0 if profile.get("location") == location else 0.2
            is_viable = offer_price >= min_price
            score = round((offer_price - distance_penalty) * 100 + min(offered_qty, quantity) / 10, 2)

            offers.append(
                {
                    "buyer_id": profile["id"],
                    "buyer_name": profile["name"],
                    "location": profile.get("location", "Market"),
                    "strategy": profile.get("strategy", "Marketplace buyer"),
                    "offered_price": offer_price,
                    "offered_quantity": round(offered_qty, 2),
                    "budget": float(profile.get("budget", 0)),
                    "target_price": float(profile.get("target_price", min_price)),
                    "status": "VIABLE" if is_viable else "BELOW_MIN_PRICE",
                    "score": score,
                }
            )

        offers.sort(key=lambda item: (item["status"] == "VIABLE", item["score"], item["offered_price"]), reverse=True)
        return offers

    def start_negotiation(
        self,
        payload: dict,
        scenario: str = "direct-sale",
        pre_id: str = None,
        live_event_callback=None,
    ):
        market_offers = self._generate_market_offers(payload)
        selected_offer = market_offers[0] if market_offers else None

        if selected_offer:
            payload = {
                **payload,
                "buyer_budget": selected_offer["budget"],
                "buyer_max_quantity": selected_offer["offered_quantity"],
                "buyer_target_price": selected_offer["target_price"],
                "buyer_location": selected_offer["location"],
            }

        farmer = self._build_farmer(payload)
        warehouse, processor, compost, transporter = self._build_support_agents(payload)
        buyer = self._build_buyer(
            {
                "name": selected_offer["buyer_name"] if selected_offer else "BuyerAgent",
                "budget": payload.get("buyer_budget", payload["quantity"] * payload["min_price"] * 1.2),
                "max_quantity": payload.get("buyer_max_quantity", payload["quantity"]),
                "target_price": payload.get("buyer_target_price", payload["min_price"] + 1),
                "location": payload.get("buyer_location", "Market"),
            }
        )

        manager = NegotiationManager(
            farmer=farmer,
            buyer=buyer,
            warehouse=warehouse,
            processor=processor,
            compost=compost,
            max_rounds=int(payload.get("max_rounds", 8)),
            live_event_callback=live_event_callback,
        )

        result = manager.start_negotiation(
            market_price=float(payload.get("market_price", payload["min_price"] + 1)),
            scenario=scenario
        )

        screening_logs = [
            f"Marketplace scan: {len(market_offers)} buyers evaluated for {payload['crop']}.",
        ]
        screening_logs.extend(
            f"{offer['buyer_name']}: bid ₹{offer['offered_price']}/kg for {offer['offered_quantity']}kg ({offer['status']})"
            for offer in market_offers
        )
        if selected_offer:
            screening_logs.append(
                f"Best buyer selected: {selected_offer['buyer_name']} at ₹{selected_offer['offered_price']}/kg before detailed negotiation."
            )
        manager.log = screening_logs + manager.log

        farmer_row = Database.upsert_farmer(
            {
                "name": payload.get("farmer_name", "Unknown Farmer"),
                "location": payload.get("location", "Unknown"),
                "language": payload.get("language", "English")
            }
        )
        produce_row = Database.create_produce(
            {
                "farmer_name": farmer_row["name"],
                "crop": payload["crop"],
                "quantity": payload["quantity"],
                "min_price": payload["min_price"],
                "shelf_life": payload.get("shelf_life", 3),
                "quality": payload.get("quality", "A"),
                "location": payload.get("location", "Unknown"),
                "language": payload.get("language", "English"),
                "status": result["state"]
            }
        )

        # Identify all agents that participated in this negotiation
        agents_involved = [farmer_row["name"]]
        if selected_offer:
            agents_involved.append(selected_offer["buyer_name"])
        if result["state"] in ("ESCALATED_STORAGE",):
            agents_involved.append("WarehouseAgent")
        elif result["state"] in ("ESCALATED_PROCESSING",):
            agents_involved.append("ProcessorAgent")
        elif result["state"] in ("ESCALATED_COMPOST",):
            agents_involved.append("CompostAgent")

        negotiation_payload = {
                "status": result["state"],
                "summary": result["summary"],
                "scenario": scenario,
                "produce_id": produce_row["id"],
                "farmer_id": farmer_row["id"],
                "farmer": farmer_row["name"],
                "crop": payload["crop"],
                "quantity": float(payload["quantity"]),
                "final_price": result["deal"].get("price") if result.get("deal") else None,
                "agents_involved": agents_involved,
                "next_action": result.get("next_action"),
                "market_offers": market_offers,
                "selected_buyer": selected_offer,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "transport_plan": {
                    "agent": transporter.name,
                    "base_fee": transporter.base_fee,
                    "capacity": transporter.vehicle_capacity,
                },
            }
        if pre_id:
            negotiation_payload["negotiation_id"] = pre_id
        negotiation_row = Database.create_negotiation(negotiation_payload)

        for idx, event in enumerate(manager.memory.get_offers(), start=1):
            offer = event["offer"]
            agent_name = event["agent"]
            if event["agent"] == "Buyer" and selected_offer:
                agent_name = selected_offer["buyer_name"]
            elif event["agent"] == "Farmer":
                agent_name = farmer_row["name"]

            Database.append_offer(
                negotiation_row["negotiation_id"],
                {
                    "round": idx,
                    "agent": agent_name,
                    "price": offer.get("price", 0),
                    "decision": offer.get("type", "OFFER"),
                    "quantity": offer.get("quantity", 0),
                    "message": offer.get("message", "")
                }
            )

        if result.get("deal"):
            Database.create_contract(
                {
                    "negotiation_id": negotiation_row["negotiation_id"],
                    "scenario": scenario,
                    "price": result["deal"].get("price", 0),
                    "quantity": result["deal"].get("quantity", 0),
                    "state": result["state"]
                }
            )

        status_payload = self._build_status_payload(negotiation_row["negotiation_id"], manager, result)
        self.active_negotiations[negotiation_row["negotiation_id"]] = status_payload

        # Persist to shared history so all users can see past negotiations
        add_history("all", {
            "negotiation_id": negotiation_row["negotiation_id"],
            "farmer": farmer_row["name"],
            "crop": payload["crop"],
            "quantity": float(payload["quantity"]),
            "status": result["state"],
            "final_price": result["deal"].get("price") if result.get("deal") else None,
            "summary": result["summary"],
            "selected_buyer": selected_offer.get("buyer_name") if selected_offer else None,
            "created_at": negotiation_row.get("created_at", ""),
            "logs": manager.log[:30],
        })

        return status_payload

    def _build_status_payload(self, negotiation_id: str, manager: NegotiationManager, result: dict):
        row = Database.negotiations.get(negotiation_id, {})
        offers = Database.get_offers_for_negotiation(negotiation_id)
        return {
            "negotiation_id": negotiation_id,
            "status": result["state"],
            "summary": result["summary"],
            "final_price": result["deal"].get("price") if result.get("deal") else None,
            "farmer": row.get("farmer"),
            "crop": row.get("crop"),
            "quantity": row.get("quantity"),
            "agents_involved": row.get("agents_involved", []),
            "offers": offers,
            "logs": manager.log,
            "events": manager.memory.get_events(),
            "price_series": manager.memory.get_price_series(),
            "next_action": result.get("next_action"),
            "deal": result.get("deal"),
            "market_offers": row.get("market_offers", []),
            "selected_buyer": row.get("selected_buyer"),
            "transport_plan": row.get("transport_plan"),
        }

    def get_negotiation_status(self, negotiation_id: str):
        if negotiation_id in self.active_negotiations:
            return self.active_negotiations[negotiation_id]

        row = Database.negotiations.get(negotiation_id)
        if not row:
            raise ValueError("Negotiation not found")

        offers = Database.get_offers_for_negotiation(negotiation_id)
        return {
            "negotiation_id": negotiation_id,
            "status": row.get("status", "UNKNOWN"),
            "summary": row.get("summary", ""),
            "farmer": row.get("farmer"),
            "crop": row.get("crop"),
            "quantity": row.get("quantity"),
            "agents_involved": row.get("agents_involved", []),
            "offers": offers,
            "next_action": row.get("next_action"),
            "final_price": row.get("final_price") or next((c.get("price") for c in Database.contracts.values() if c.get("negotiation_id") == negotiation_id), None),
            "market_offers": row.get("market_offers", []),
            "selected_buyer": row.get("selected_buyer"),
            "transport_plan": row.get("transport_plan"),
        }

    def list_agents(self):
        return [
            {"role": "Farmer", "capability": "Sell produce"},
            {"role": "Buyer", "capability": "Purchase produce"},
            {"role": "Warehouse", "capability": "Store produce"},
            {"role": "Transporter", "capability": "Move goods"},
            {"role": "Processor", "capability": "Buy for processing"},
            {"role": "Compost", "capability": "Fallback spoilage channel"},
        ]


service = NegotiationService()


def start_negotiation(payload: dict, scenario: str = "direct-sale"):
    return service.start_negotiation(payload, scenario=scenario)


def get_negotiation_status(negotiation_id: str):
    return service.get_negotiation_status(negotiation_id)


def list_agents():
    return service.list_agents()


def list_farmers():
    return list(Database.farmers.values())


def list_negotiations():
    negs = list(Database.negotiations.values())
    negs.reverse()
    return negs[:50]


def list_buyers():
    service._ensure_default_buyers()
    return Database.list_buyers()


def list_produce():
    return Database.list_produce()
