import random
import time


class MarketSimulator:
    """
    MarketSimulator generates dynamic market conditions
    that affect negotiations in the agricultural supply chain.

    It simulates:
    - buyer demand
    - supply levels
    - buyer appearance
    - market price fluctuations
    - spoilage pressure
    """

    def __init__(self):

        # Market conditions
        self.market_price = 18
        self.demand_level = "normal"
        self.supply_level = "normal"

        # Active buyers in market
        self.active_buyers = []

        # Event history
        self.market_events = []

    # ---------------------------------------------------
    # Generate Market Demand Level
    # ---------------------------------------------------

    def generate_demand(self):

        demand_states = ["low", "normal", "high"]

        self.demand_level = random.choice(demand_states)

        event = f"Market demand changed to {self.demand_level}"

        self.market_events.append(event)

        return self.demand_level

    # ---------------------------------------------------
    # Generate Supply Level
    # ---------------------------------------------------

    def generate_supply(self):

        supply_states = ["low", "normal", "high"]

        self.supply_level = random.choice(supply_states)

        event = f"Market supply changed to {self.supply_level}"

        self.market_events.append(event)

        return self.supply_level

    # ---------------------------------------------------
    # Adjust Market Price Based on Supply & Demand
    # ---------------------------------------------------

    def update_market_price(self):

        base_price = self.market_price

        if self.demand_level == "high" and self.supply_level == "low":
            base_price += random.randint(2, 4)

        elif self.demand_level == "low" and self.supply_level == "high":
            base_price -= random.randint(2, 4)

        elif self.demand_level == "high":
            base_price += random.randint(1, 2)

        elif self.supply_level == "high":
            base_price -= random.randint(1, 2)

        # Ensure price does not drop below 5
        base_price = max(base_price, 5)

        self.market_price = base_price

        event = f"Market price adjusted to ₹{self.market_price}/kg"

        self.market_events.append(event)

        return self.market_price

    # ---------------------------------------------------
    # Simulate Buyer Appearance
    # ---------------------------------------------------

    def simulate_buyer_appearance(self):

        chance = random.random()

        if chance > 0.5:

            buyer = {
                "buyer_id": f"buyer_{len(self.active_buyers) + 1}",
                "budget": random.randint(5000, 30000),
                "target_price": random.randint(
                    self.market_price - 3,
                    self.market_price + 2
                ),
                "max_quantity": random.randint(200, 1000)
            }

            self.active_buyers.append(buyer)

            event = f"New buyer entered market: {buyer['buyer_id']}"

            self.market_events.append(event)

            return buyer

        return None

    # ---------------------------------------------------
    # Simulate Buyer Leaving Market
    # ---------------------------------------------------

    def simulate_buyer_exit(self):

        if not self.active_buyers:
            return None

        chance = random.random()

        if chance > 0.6:

            leaving_buyer = random.choice(self.active_buyers)

            self.active_buyers.remove(leaving_buyer)

            event = f"Buyer left market: {leaving_buyer['buyer_id']}"

            self.market_events.append(event)

            return leaving_buyer

        return None

    # ---------------------------------------------------
    # Simulate Spoilage Pressure
    # ---------------------------------------------------

    def simulate_spoilage(self, farmer):

        if farmer.shelf_life <= 1:

            event = "Spoilage risk HIGH — farmer must sell quickly"

            self.market_events.append(event)

            return "high"

        if farmer.shelf_life <= 2:

            event = "Spoilage risk moderate"

            self.market_events.append(event)

            return "medium"

        return "low"

    # ---------------------------------------------------
    # Run Market Tick (One Simulation Step)
    # ---------------------------------------------------

    def run_market_cycle(self):

        """
        Runs one market cycle where supply, demand,
        price and buyers may change.
        """

        self.generate_demand()

        self.generate_supply()

        self.update_market_price()

        new_buyer = self.simulate_buyer_appearance()

        exiting_buyer = self.simulate_buyer_exit()

        cycle_summary = {
            "market_price": self.market_price,
            "demand": self.demand_level,
            "supply": self.supply_level,
            "active_buyers": len(self.active_buyers),
            "new_buyer": new_buyer,
            "buyer_exit": exiting_buyer
        }

        return cycle_summary

    # ---------------------------------------------------
    # Get Market Status
    # ---------------------------------------------------

    def get_market_status(self):

        return {
            "market_price": self.market_price,
            "demand_level": self.demand_level,
            "supply_level": self.supply_level,
            "active_buyers": self.active_buyers
        }

    # ---------------------------------------------------
    # Get Market Events
    # ---------------------------------------------------

    def get_market_events(self):

        return self.market_events

    # ---------------------------------------------------
    # Debug Run
    # ---------------------------------------------------

if __name__ == "__main__":

    simulator = MarketSimulator()

    print("\n--- Market Simulation ---\n")

    for i in range(5):

        cycle = simulator.run_market_cycle()

        print(f"\nCycle {i+1}")
        print(cycle)

        time.sleep(1)

    print("\nMarket Events:\n")

    for event in simulator.get_market_events():
        print(event)