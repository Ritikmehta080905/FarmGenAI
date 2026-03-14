from intelligence.llm_client import LLMClient

# Initialize the LLM client
client = LLMClient()

# Sample prompt for testing
prompt = "You are a farmer agent. Crop: Tomato, Quantity: 1000kg, Minimum price: 18. Buyer offered 16. Decide next action."

# Get LLM decision
decision = client.get_completion(prompt)

print("LLM Response:")
print(decision)