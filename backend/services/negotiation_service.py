from ...agents.negotiation_engine import simulate_negotiation
import uuid

class NegotiationService:
    def __init__(self):
        self.active_negotiations = {}

    def start_negotiation(self, farmer_id, buyer_id):
        negotiation_id = str(uuid.uuid4())
        # In a real app, initialize agents based on IDs
        self.active_negotiations[negotiation_id] = {
            "farmer_id": farmer_id,
            "buyer_id": buyer_id,
            "status": "started",
            "offers": []
        }
        return negotiation_id

    def make_offer(self, negotiation_id, offer):
        if negotiation_id not in self.active_negotiations:
            raise ValueError("Negotiation not found")
        
        # For simplicity, run the simulation
        result = simulate_negotiation()
        self.active_negotiations[negotiation_id]["status"] = "completed"
        return {"result": result}

    def get_negotiation_status(self, negotiation_id):
        if negotiation_id not in self.active_negotiations:
            raise ValueError("Negotiation not found")
        return self.active_negotiations[negotiation_id]
