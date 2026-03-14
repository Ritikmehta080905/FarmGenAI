# test_featherless_connection.py
from intelligence.llm_client import LLMClient

try:
    client = LLMClient()
    prompt = "Say hello in one sentence."
    response = client.generate_response(prompt)
    print("✅ API Connected. Response from Featherless:")
    print(response)
except Exception as e:
    print("❌ API connection failed:", e)