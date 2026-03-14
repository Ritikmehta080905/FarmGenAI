from llm.negotiation_reasoning import farmer_decision

result = farmer_decision(
    min_price=18,
    buyer_offer=16,
    spoilage_days=3
)

print(result)