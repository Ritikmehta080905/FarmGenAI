from agents.buyer_agent import BuyerAgent
from agents.compost_agent import CompostAgent
from agents.farmer_agent import FarmerAgent
from agents.processor_agent import ProcessorAgent
from agents.transporter_agent import TransporterAgent
from agents.warehouse_agent import WarehouseAgent
from database.db import Database
from negotiation_engine.negotiation_manager import NegotiationManager


class NegotiationService:
    def __init__(self):
        self.active_negotiations = {}

    def start_negotiation(self, payload: dict, scenario: str = "direct-sale"):
        farmer = FarmerAgent(
            name=payload.get("farmer_name", "FarmerAgent"),
            crop=payload["crop"],
            quantity=float(payload["quantity"]),
            min_price=float(payload["min_price"]),
            shelf_life=int(payload.get("shelf_life", 3)),
            location=payload.get("location")
        )

        buyer = BuyerAgent(
            name="BuyerAgent",
            budget=float(payload.get("buyer_budget", payload["quantity"] * payload["min_price"] * 1.2)),
            max_quantity=int(payload.get("buyer_max_quantity", payload["quantity"])),
            target_price=float(payload.get("buyer_target_price", payload["min_price"] + 1)),
            location=payload.get("buyer_location", "Market")
        )

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

        manager = NegotiationManager(
            farmer=farmer,
            buyer=buyer,
            warehouse=warehouse,
            processor=processor,
            compost=compost,
            max_rounds=int(payload.get("max_rounds", 8))
        )

        result = manager.start_negotiation(
            market_price=float(payload.get("market_price", payload["min_price"] + 1)),
            scenario=scenario
        )

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
                "status": "NEGOTIATING"
            }
        )

        negotiation_row = Database.create_negotiation(
            {
                "status": result["state"],
                "summary": result["summary"],
                "scenario": scenario,
                "produce_id": produce_row["id"],
                "farmer_id": farmer_row["id"],
                "next_action": result.get("next_action")
            }
        )

        for idx, event in enumerate(manager.memory.get_offers(), start=1):
            offer = event["offer"]
            Database.append_offer(
                negotiation_row["negotiation_id"],
                {
                    "round": idx,
                    "agent": event["agent"],
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
        return status_payload

    def _build_status_payload(self, negotiation_id: str, manager: NegotiationManager, result: dict):
        offers = Database.get_offers_for_negotiation(negotiation_id)
        return {
            "negotiation_id": negotiation_id,
            "status": result["state"],
            "summary": result["summary"],
            "final_price": result["deal"].get("price") if result.get("deal") else None,
            "offers": offers,
            "logs": manager.log,
            "events": manager.memory.get_events(),
            "price_series": manager.memory.get_price_series(),
            "next_action": result.get("next_action"),
            "deal": result.get("deal")
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
            "offers": offers,
            "next_action": row.get("next_action"),
            "final_price": next((c.get("price") for c in Database.contracts.values() if c.get("negotiation_id") == negotiation_id), None),
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


def list_produce():
    return list(Database.produce.values())
