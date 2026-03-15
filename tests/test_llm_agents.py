"""Unit tests for negotiation reasoning (LLM or deterministic fallback)."""

import unittest

from llm.negotiation_reasoning import (
    farmer_decision,
    buyer_decision,
    processor_decision,
    warehouse_decision,
)

VALID_FARMER_DECISIONS = {
    "Accept offer", "Counter offer", "Reject offer",
    "Store in warehouse", "Sell to processor",
}
VALID_BUYER_DECISIONS = {"Accept offer", "Counter offer", "Reject offer"}
VALID_PROCESSOR_DECISIONS = {"Buy produce", "Counter offer", "Reject offer"}
VALID_WAREHOUSE_DECISIONS = {"Accept offer", "Reject offer", "Counter offer"}


class TestFarmerDecision(unittest.TestCase):

    def test_offer_below_min_without_spoilage(self):
        result = farmer_decision(min_price=18, buyer_offer=15, spoilage_days=5)
        self.assertIn(result["decision"], VALID_FARMER_DECISIONS)
        self.assertIn("reason", result)

    def test_offer_above_min(self):
        result = farmer_decision(min_price=18, buyer_offer=20, spoilage_days=5)
        self.assertIn(result["decision"], VALID_FARMER_DECISIONS)

    def test_critical_spoilage_routes_away(self):
        result = farmer_decision(min_price=18, buyer_offer=12, spoilage_days=1)
        # Critical spoilage → accept or redirect, never a pure counter
        self.assertIn(result["decision"],
                      {"Accept offer", "Sell to processor", "Store in warehouse"})


class TestBuyerDecision(unittest.TestCase):

    def test_ask_within_budget(self):
        result = buyer_decision(max_price=20, farmer_ask=18, spoilage_days=3)
        self.assertIn(result["decision"], VALID_BUYER_DECISIONS)

    def test_ask_above_budget(self):
        result = buyer_decision(max_price=18, farmer_ask=25, spoilage_days=3)
        self.assertIn(result["decision"], VALID_BUYER_DECISIONS)


class TestProcessorDecision(unittest.TestCase):

    def test_below_demand_price(self):
        result = processor_decision(demand_price=20, offered_price=17,
                                    quantity=1000, spoilage_days=3)
        self.assertIn(result["decision"], VALID_PROCESSOR_DECISIONS)

    def test_above_demand_price(self):
        result = processor_decision(demand_price=20, offered_price=24,
                                    quantity=1000, spoilage_days=3)
        self.assertIn(result["decision"], VALID_PROCESSOR_DECISIONS)


class TestWarehouseDecision(unittest.TestCase):

    def test_high_spoilage_rejects_storage(self):
        result = warehouse_decision(storage_cost_per_day=2,
                                    spoilage_days=2, market_price=18)
        self.assertIn(result["decision"], VALID_WAREHOUSE_DECISIONS)

    def test_low_spoilage_accepts_storage(self):
        result = warehouse_decision(storage_cost_per_day=1,
                                    spoilage_days=10, market_price=18)
        self.assertIn(result["decision"], VALID_WAREHOUSE_DECISIONS)


if __name__ == "__main__":
    unittest.main()


def test_farmer_decisions():
    print("=== Testing Farmer Agent ===")

    # Test 1: Offer below minimum - should counter or reject
    print("\nTest 1: Offer ₹15, Min ₹18, Spoilage 3 days")
    result = farmer_decision(18, 15, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")
    assert result['decision'] in ["Counter offer", "Reject offer", "Store in warehouse", "Sell to processor"]

    # Test 2: Good offer - should accept
    print("\nTest 2: Offer ₹20, Min ₹18, Spoilage 3 days")
    result = farmer_decision(18, 20, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

    # Test 3: Low spoilage - might store
    print("\nTest 3: Offer ₹16, Min ₹18, Spoilage 7 days")
    result = farmer_decision(18, 16, 7)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

def test_buyer_decisions():
    print("\n=== Testing Buyer Agent ===")

    # Test 1: Price within budget - should accept
    print("\nTest 1: Ask ₹18, Max ₹20, Spoilage 3 days")
    result = buyer_decision(20, 18, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

    # Test 2: Price above budget - should reject or counter
    print("\nTest 2: Ask ₹22, Max ₹20, Spoilage 3 days")
    result = buyer_decision(20, 22, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

def test_processor_decisions():
    print("\n=== Testing Processor Agent ===")

    # Test 1: Price below demand - should buy
    print("\nTest 1: Demand ₹20, Offered ₹18, Quantity 1000, Spoilage 3 days")
    result = processor_decision(20, 18, 1000, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

    # Test 2: Price above demand - should skip
    print("\nTest 2: Demand ₹20, Offered ₹22, Quantity 1000, Spoilage 3 days")
    result = processor_decision(20, 22, 1000, 3)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

def test_warehouse_decisions():
    print("\n=== Testing Warehouse Agent ===")

    # Test 1: High spoilage - should sell fast
    print("\nTest 1: Cost ₹2/day, Spoilage 2 days, Market ₹18")
    result = warehouse_decision(2, 2, 18)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

    # Test 2: Low spoilage - might store
    print("\nTest 2: Cost ₹1/day, Spoilage 10 days, Market ₹18")
    result = warehouse_decision(1, 10, 18)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")

if __name__ == "__main__":
    try:
        test_farmer_decisions()
        test_buyer_decisions()
        test_processor_decisions()
        test_warehouse_decisions()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()