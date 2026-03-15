"""Unit tests for FarmerAgent, BuyerAgent, WarehouseAgent."""

import unittest

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from agents.warehouse_agent import WarehouseAgent


MARKET_PRICE = 18
CONTEXT = {"market_price": MARKET_PRICE, "round": 1}


class TestFarmerAgent(unittest.TestCase):

    def setUp(self):
        self.farmer = FarmerAgent(
            name="TestFarmer",
            crop="Tomato",
            quantity=500,
            min_price=18,
            shelf_life=4,
        )

    def test_initial_price_above_min(self):
        self.assertGreaterEqual(self.farmer.current_price, self.farmer.min_price)

    def test_make_offer_returns_price_and_quantity(self):
        offer = self.farmer.make_offer(CONTEXT)
        self.assertIn("price", offer)
        self.assertIn("quantity", offer)
        self.assertGreater(offer["price"], 0)

    def test_evaluate_offer_accept_when_price_meets_min(self):
        result = self.farmer.evaluate_offer({"price": 20, "quantity": 500})
        self.assertEqual(result, "ACCEPT")

    def test_evaluate_offer_counter_when_price_below_min(self):
        result = self.farmer.evaluate_offer({"price": 10, "quantity": 500})
        self.assertEqual(result, "COUNTER")

    def test_respond_to_offer_returns_dict(self):
        buyer_offer = {"price": 15, "quantity": 400, "type": "OFFER",
                       "message": "test"}
        result = self.farmer.respond_to_offer(buyer_offer, CONTEXT)
        self.assertIn("price", result)
        self.assertIn("type", result)


class TestBuyerAgent(unittest.TestCase):

    def setUp(self):
        self.buyer = BuyerAgent(
            name="TestBuyer",
            budget=10000,
            max_quantity=600,
            target_price=16,
        )

    def test_make_offer_returns_price_and_quantity(self):
        offer = self.buyer.make_offer(CONTEXT)
        self.assertIn("price", offer)
        self.assertIn("quantity", offer)

    def test_make_offer_price_at_most_target(self):
        offer = self.buyer.make_offer(CONTEXT)
        self.assertLessEqual(offer["price"], self.buyer.target_price + 5)

    def test_respond_to_offer_returns_dict(self):
        farmer_offer = {"price": 20, "quantity": 500, "type": "OFFER",
                        "message": "test"}
        result = self.buyer.respond_to_offer(farmer_offer, CONTEXT)
        self.assertIn("price", result)


class TestWarehouseAgent(unittest.TestCase):

    def setUp(self):
        self.warehouse = WarehouseAgent(
            name="TestWarehouse",
            capacity=5000,
            storage_cost_per_kg=1.5,
            location="Nashik",
        )

    def test_available_capacity_initial(self):
        self.assertEqual(self.warehouse.available_capacity(), 5000)

    def test_respond_to_offer_accept(self):
        result = self.warehouse.respond_to_offer({"quantity": 200, "crop": "Tomato"})
        self.assertIn(result["type"], ("ACCEPT_STORAGE", "REJECT"))

    def test_respond_to_offer_reject_when_over_capacity(self):
        result = self.warehouse.respond_to_offer({"quantity": 99999, "crop": "Tomato"})
        self.assertEqual(result["type"], "REJECT")


if __name__ == "__main__":
    unittest.main()
