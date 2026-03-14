#!/usr/bin/env python3
"""
Test script to validate LLM agent decisions
"""

from llm.negotiation_reasoning import farmer_decision, buyer_decision, processor_decision, warehouse_decision

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