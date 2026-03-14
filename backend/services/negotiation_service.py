from database.db import Database
from backend.services.pricing_service import calculate_counter_offer
from backend.services.storage_service import assign_storage
from backend.services.history_service import add_history


def list_farmers():
    return list(Database.farmers.values())


def list_buyers():
    return [
        {"name": "Mumbai Market", "crop": "Tomato"},
        {"name": "Pune Wholesale", "crop": "Onion"},
        {"name": "Nashik Trader", "crop": "Grapes"}
    ]


def list_warehouses():
    return [
        {"name": "Nashik Storage", "capacity": 5000},
        {"name": "Pune Cold Storage", "capacity": 3000}
    ]


def start_negotiation(data: dict):
    produce_id = Database.generate_id("produce")
    negotiation_id = Database.generate_id("neg")

    produce_record = {
        "id": produce_id,
        "farmer_name": data.get("farmer_name", "Unknown Farmer"),
        "crop": data["crop"],
        "quantity": data["quantity"],
        "min_price": data["min_price"],
        "shelf_life": data["shelf_life"],
        "location": data["location"],
        "quality": data.get("quality", "A"),
        "language": data.get("language", "Marathi"),
        "status": "listed"
    }

    Database.produce[produce_id] = produce_record

    buyer_offer = data["min_price"] - 2
    offers = []
    final_price = None
    next_action = None

    offers.append({
        "round": 1,
        "agent": "Buyer",
        "price": buyer_offer,
        "decision": "offer"
    })

    if buyer_offer >= data["min_price"]:
        status = "deal"
        final_price = buyer_offer
        summary = f"Buyer accepted directly at ₹{final_price}/kg."
        next_action = "Assign transport"
    else:
        counter = calculate_counter_offer(data["min_price"], buyer_offer)

        offers.append({
            "round": 2,
            "agent": "Farmer",
            "price": counter,
            "decision": "counter"
        })

        if counter <= buyer_offer + 1:
            status = "deal"
            final_price = counter
            summary = f"Deal closed after counter-offer at ₹{final_price}/kg."
            next_action = "Assign transport"
        else:
            if data["shelf_life"] > 2:
                storage = assign_storage(data)

                offers.append({
                    "round": 3,
                    "agent": "Warehouse",
                    "price": 0,
                    "decision": "store"
                })

                status = "storage"
                summary = f"No buyer matched. Produce moved to {storage['warehouse']}."
                next_action = "Wait for better buyer"
            else:
                processor_price = max(data["min_price"] - 4, 1)

                offers.append({
                    "round": 3,
                    "agent": "Processor",
                    "price": processor_price,
                    "decision": "processor"
                })

                status = "processor"
                final_price = processor_price
                summary = f"Low shelf life. Sent to processor at ₹{final_price}/kg."
                next_action = "Complete processor sale"

    negotiation_record = {
        "negotiation_id": negotiation_id,
        "produce_id": produce_id,
        "status": status,
        "offers": offers,
        "summary": summary,
        "final_price": final_price,
        "next_action": next_action
    }

    Database.negotiations[negotiation_id] = negotiation_record
    Database.offers[negotiation_id] = offers

    user_id = data.get("user_id")
    if user_id:
        add_history(user_id, {
            "negotiation_id": negotiation_id,
            "crop": data["crop"],
            "quantity": data["quantity"],
            "status": status,
            "final_price": final_price,
            "summary": summary
        })

    return {
        "negotiation_id": negotiation_id,
        "status": status,
        "offers": offers
    }


def get_negotiation_status(negotiation_id: str):
    record = Database.negotiations.get(negotiation_id)

    if not record:
        return {
            "negotiation_id": negotiation_id,
            "status": "not_found",
            "offers": [],
            "summary": "Negotiation ID not found",
            "final_price": None,
            "next_action": None
        }

    return {
        "negotiation_id": record["negotiation_id"],
        "status": record["status"],
        "offers": record["offers"],
        "summary": record["summary"],
        "final_price": record["final_price"],
        "next_action": record["next_action"]
    }


def list_produce():
    return list(Database.produce.values())