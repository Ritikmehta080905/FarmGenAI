from negotiation_engine.negotiation_manager import NegotiationManager
from simulation.agent_initializer import initialize_agents
from simulation.market_simulator import MarketSimulator
from simulation.metrics_tracker import MetricsTracker


class MarketScenario:
    """
    Runs a market scenario with farmer and buyer agents,
    using LLM-assisted decision-making.
    """

    def __init__(self):
        self.scenarios = []
        self.market = MarketSimulator()
        self.metrics = MetricsTracker()

    # ----------------------------------------
    # Run multiple scenarios
    # ----------------------------------------
    def run_all(self):
        results = []

        for scenario in self.scenarios:
            result = self.run_scenario(scenario)
            results.append(result)
            self.metrics.record_result(scenario["name"], result["result"])

        return {
            "scenarios": results,
            "metrics": self.metrics.summarize()
        }

    # ----------------------------------------
    # Single scenario runner
    # ----------------------------------------
    def run_scenario(self, scenario):
        market_tick = self.market.run_market_cycle()
        agents = initialize_agents(
            {
                "crop": scenario["crop"],
                "quantity": scenario["farmer_quantity"],
                "min_price": scenario["farmer_min_price"],
                "shelf_life": scenario["shelf_life"],
                "buyer_budget": scenario["buyer_budget"],
                "buyer_max_quantity": scenario["buyer_max_quantity"],
                "buyer_target_price": scenario["buyer_target_price"],
                "market_price": market_tick["market_price"],
                "location": scenario.get("location", "Nashik")
            }
        )

        # Start negotiation
        manager = NegotiationManager(
            farmer=agents["farmer"],
            buyer=agents["buyer"],
            warehouse=agents["warehouse"],
            processor=agents["processor"],
            compost=agents["compost"],
            max_rounds=scenario.get("max_rounds", 10)
        )
        result = manager.start_negotiation(
            market_price=market_tick["market_price"],
            scenario=scenario.get("scenario_type", "direct-sale")
        )

        return {
            "scenario": scenario["name"],
            "market_tick": market_tick,
            "result": result,
            "logs": manager.log,
            "price_series": manager.memory.get_price_series()
        }

    # ----------------------------------------
    # Add scenario
    # ----------------------------------------
    def add_scenario(self, name, crop, farmer_quantity, farmer_min_price,
                     buyer_budget, buyer_max_quantity, buyer_target_price,
                     shelf_life=5, max_rounds=10, scenario_type="direct-sale"):
        self.scenarios.append({
            "name": name,
            "crop": crop,
            "farmer_quantity": farmer_quantity,
            "farmer_min_price": farmer_min_price,
            "buyer_budget": buyer_budget,
            "buyer_max_quantity": buyer_max_quantity,
            "buyer_target_price": buyer_target_price,
            "shelf_life": shelf_life,
            "max_rounds": max_rounds,
            "scenario_type": scenario_type,
        })


def run_default_simulation():
    runner = MarketScenario()
    runner.add_scenario(
        name="Direct Sale",
        crop="Tomato",
        farmer_quantity=1000,
        farmer_min_price=18,
        buyer_budget=20000,
        buyer_max_quantity=600,
        buyer_target_price=18,
        shelf_life=4,
        max_rounds=8,
        scenario_type="direct-sale",
    )
    runner.add_scenario(
        name="Storage Fallback",
        crop="Tomato",
        farmer_quantity=1300,
        farmer_min_price=21,
        buyer_budget=18000,
        buyer_max_quantity=600,
        buyer_target_price=16,
        shelf_life=3,
        max_rounds=7,
        scenario_type="storage",
    )
    return runner.run_all()


if __name__ == "__main__":
    print(run_default_simulation())