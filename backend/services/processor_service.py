"""
backend/services/processor_service.py

Processor / Value-Added Processing Service — FR-11

Manages industrial processor listings and order submission for
crops that failed direct sale and are escalated to processing.
"""

import uuid
from datetime import datetime, timezone
from copy import deepcopy
from typing import Dict, List

_PROCESSOR_CATALOG: List[Dict] = [
    {
        "processor_id": "proc_agro_industrial_01",
        "name": "Maharashtra Agro Processing Ltd",
        "crop_types": ["Tomato", "Onion", "Potato", "Cabbage", "Cauliflower"],
        "price_per_kg": 14.5,
        "capacity_kg": 5000,
        "location": "Aurangabad",
        "output_product": "Paste / Puree",
        "min_order_kg": 200,
    },
    {
        "processor_id": "proc_dehydration_nashik",
        "name": "Nashik Dehydration Plant",
        "crop_types": ["Onion", "Garlic", "Tomato", "Ginger"],
        "price_per_kg": 16.0,
        "capacity_kg": 3000,
        "location": "Nashik",
        "output_product": "Dehydrated Flakes / Powder",
        "min_order_kg": 100,
    },
    {
        "processor_id": "proc_juice_pune",
        "name": "Pune Fresh Juice Corp",
        "crop_types": ["Mango", "Tomato", "Guava", "Citrus", "Pomegranate"],
        "price_per_kg": 18.0,
        "capacity_kg": 2000,
        "location": "Pune",
        "output_product": "Cold-Pressed Juice",
        "min_order_kg": 150,
    },
    {
        "processor_id": "proc_pickle_kolhapur",
        "name": "Kolhapur Pickle & Pickle Works",
        "crop_types": ["Mango", "Lemon", "Cabbage", "Cauliflower", "Garlic"],
        "price_per_kg": 15.5,
        "capacity_kg": 1500,
        "location": "Kolhapur",
        "output_product": "Pickles / Preserves",
        "min_order_kg": 50,
    },
]

# In-memory order store
_processor_orders: Dict[str, Dict] = {}


async def list_processors(crop: str = None) -> List[Dict]:
    """List available processors, optionally filtered by crop type."""
    if not crop:
        return deepcopy(_PROCESSOR_CATALOG)
    return [
        deepcopy(p) for p in _PROCESSOR_CATALOG
        if any(crop.lower() in c.lower() for c in p["crop_types"])
    ]


async def submit_processing_order(order: Dict) -> Dict:
    """
    Submit a crop lot to a processor.

    Required fields: negotiation_id, processor_id, crop, quantity, farmer_id
    """
    processor_id = order.get("processor_id")
    processor = next((p for p in _PROCESSOR_CATALOG if p["processor_id"] == processor_id), None)
    if not processor:
        raise ValueError(f"Processor '{processor_id}' not found.")

    quantity = float(order.get("quantity", 0))
    if quantity < processor["min_order_kg"]:
        raise ValueError(
            f"Minimum order for {processor['name']} is {processor['min_order_kg']} kg. Got {quantity} kg."
        )
    if quantity > processor["capacity_kg"]:
        raise ValueError(
            f"Order exceeds processor capacity ({processor['capacity_kg']} kg). Got {quantity} kg."
        )

    total_payment = round(processor["price_per_kg"] * quantity, 2)
    order_id = f"porder_{str(uuid.uuid4())[:8]}"

    record = {
        "order_id": order_id,
        "processor_id": processor_id,
        "processor_name": processor["name"],
        "negotiation_id": order.get("negotiation_id"),
        "farmer_id": order.get("farmer_id"),
        "crop": order.get("crop"),
        "quantity": quantity,
        "price_per_kg": processor["price_per_kg"],
        "total_payment": total_payment,
        "output_product": processor["output_product"],
        "status": "SUBMITTED",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    _processor_orders[order_id] = record
    return record


async def get_processor_order(order_id: str) -> Dict:
    """Retrieve a processor order by ID."""
    order = _processor_orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return order


async def list_processor_orders(farmer_id: str = None) -> List[Dict]:
    """List all processing orders, optionally filtered by farmer."""
    orders = list(_processor_orders.values())
    if farmer_id:
        orders = [o for o in orders if o.get("farmer_id") == farmer_id]
    return orders

