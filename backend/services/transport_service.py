from datetime import datetime, timedelta, timezone


_FLEET = [
    {
        "vehicle_id": "veh_small_01",
        "vehicle_name": "Mini Truck 01",
        "capacity_kg": 1200.0,
        "base_fee": 280.0,
        "cost_per_km_per_kg": 0.028,
    },
    {
        "vehicle_id": "veh_mid_07",
        "vehicle_name": "Cargo Truck 07",
        "capacity_kg": 3000.0,
        "base_fee": 430.0,
        "cost_per_km_per_kg": 0.024,
    },
    {
        "vehicle_id": "veh_heavy_12",
        "vehicle_name": "Heavy Carrier 12",
        "capacity_kg": 6500.0,
        "base_fee": 690.0,
        "cost_per_km_per_kg": 0.019,
    },
]


def list_fleet():
    return list(_FLEET)


def assign_transport(shipment: dict):
    quantity = float(shipment.get("quantity", 0) or 0)
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    distance_km = float(shipment.get("distance_km", 60) or 60)
    if distance_km <= 0:
        raise ValueError("distance_km must be greater than 0")

    shelf_life = int(shipment.get("shelf_life", 3) or 3)

    candidates = [vehicle for vehicle in _FLEET if vehicle["capacity_kg"] >= quantity]
    if not candidates:
        raise ValueError("No vehicle can handle this shipment quantity")

    selected = sorted(candidates, key=lambda vehicle: (vehicle["capacity_kg"], vehicle["base_fee"]))[0]

    perishability_multiplier = 1.2 if shelf_life <= 2 else 1.0
    transit_hours = max(2, round(distance_km / 28))
    pickup_eta_hours = 1 if shelf_life <= 2 else 3
    pickup_time = datetime.now(timezone.utc) + timedelta(hours=pickup_eta_hours)

    variable_cost = distance_km * quantity * selected["cost_per_km_per_kg"]
    total_cost = round((selected["base_fee"] + variable_cost) * perishability_multiplier, 2)

    return {
        "vehicle_id": selected["vehicle_id"],
        "truck": selected["vehicle_name"],
        "capacity_kg": selected["capacity_kg"],
        "quantity": quantity,
        "distance_km": distance_km,
        "pickup_time": pickup_time.isoformat(),
        "estimated_transit_hours": transit_hours,
        "estimated_cost": total_cost,
        "status": "SCHEDULED",
    }