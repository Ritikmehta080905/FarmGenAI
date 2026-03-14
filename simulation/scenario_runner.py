
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from agents.warehouse_agent import WarehouseAgent
from agents.processor_agent import ProcessorAgent
from agents.transporter_agent import TransportAgent

from negotiation_engine.negotiation_manager import NegotiationManager


class ScenarioRunner:
    """
    ScenarioRunner is responsible for running
    different agricultural supply chain scenarios.

    It creates agents, starts negotiations,
    and returns logs + final results.
    """

    def __init__(self):

        self.logs = []
        self.results = {}

    # -------------------------------------------------
    # Utility Logging
    # -------------------------------------------------

    def log(self, message):

        print(message)
        self.logs.append(message)

    # -------------------------------------------------
    # Scenario 1 — Direct Sale
    # Farmer → Buyer → Transport
    # -------------------------------------------------

    def run_direct_sale(self):

        self.log("\n===== Scenario 1: Direct Sale =====")

        farmer = FarmerAgent(
            name="FarmerAgent",
            crop="Tomato",
            quantity=1000,
            min_price=18,
            shelf_life=4
        )

        buyer = BuyerAgent(
            name="BuyerAgent",
            budget=20000,
            max_quantity=600,
            target_price=18
        )

        transporter = TransportAgent(
            name="TransportAgent",
            vehicle_capacity=2000,
            cost_per_km_per_kg=0.02,
            base_fee=200
        )

        manager = NegotiationManager(farmer, buyer)

        deal_success = manager.start_negotiation()

        self.logs.extend(manager.log)

        if deal_success:

            deal = manager.memory.get_deal()

            quantity = deal["quantity"]
            distance = 120  # simulated distance

            transport_offer = transporter.respond_to_offer(
                {
                    "quantity": quantity,
                    "distance": distance
                }
            )

            self.logs.append(transport_offer["message"])

            self.results = {
                "scenario": "direct_sale",
                "deal": deal,
                "transport": transport_offer
            }

            return True

        self.results = {
            "scenario": "direct_sale",
            "deal": None
        }

        return False

    # -------------------------------------------------
    # Scenario 2 — Storage (No Buyer)
    # Farmer → Warehouse
    # -------------------------------------------------

    def run_storage_scenario(self):

        self.log("\n===== Scenario 2: Storage =====")

        farmer = FarmerAgent(
            name="FarmerAgent",
            crop="Tomato",
            quantity=1000,
            min_price=20,
            shelf_life=4
        )

        warehouse = WarehouseAgent(
            name="WarehouseAgent",
            capacity=5000,
            storage_cost_per_kg=2
        )

        storage_request = {
            "quantity": farmer.quantity,
            "crop": farmer.crop
        }

        response = warehouse.respond_to_offer(storage_request)

        self.logs.append(response["message"])

        if response["type"] == "ACCEPT_STORAGE":

            self.results = {
                "scenario": "storage",
                "stored_quantity": response["quantity"],
                "storage_cost": response["cost"]
            }

            return True

        self.results = {
            "scenario": "storage",
            "stored_quantity": 0
        }

        return False

    # -------------------------------------------------
    # Scenario 3 — Processing (Spoilage)
    # Farmer → Processor
    # -------------------------------------------------

    def run_processing_scenario(self):

        self.log("\n===== Scenario 3: Processing =====")

        farmer = FarmerAgent(
            name="FarmerAgent",
            crop="Tomato",
            quantity=800,
            min_price=18,
            shelf_life=1
        )

        processor = ProcessorAgent(
            name="ProcessorAgent",
            crop_type="Tomato",
            processing_capacity=1000,
            processing_cost_per_kg=4,
            target_price=12,
            max_price=16
        )

        # Farmer makes offer
        farmer_offer = farmer.make_offer()

        response = processor.respond_to_offer(farmer_offer)

        self.logs.append(response["message"])

        if response["type"] == "ACCEPT":

            self.results = {
                "scenario": "processing",
                "quantity_processed": response["quantity"],
                "price": response["price"]
            }

            return True

        self.results = {
            "scenario": "processing",
            "result": "processor rejected"
        }

        return False

    # -------------------------------------------------
    # Run Scenario By Name
    # -------------------------------------------------

    def run(self, scenario_name):

        if scenario_name == "direct_sale":
            return self.run_direct_sale()

        if scenario_name == "storage":
            return self.run_storage_scenario()

        if scenario_name == "processing":
            return self.run_processing_scenario()

        raise ValueError(f"Unknown scenario: {scenario_name}")

    # -------------------------------------------------
    # Get Logs
    # -------------------------------------------------

    def get_logs(self):

        return self.logs

    # -------------------------------------------------
    # Get Results
    # -------------------------------------------------

    def get_results(self):

        return self.results


# -------------------------------------------------
# Standalone execution
# -------------------------------------------------

if __name__ == "__main__":

    runner = ScenarioRunner()

    runner.run("direct_sale")

    print("\n--- Simulation Logs ---\n")

    for log in runner.get_logs():
        print(log)

    print("\n--- Final Result ---\n")
    print(runner.get_results())