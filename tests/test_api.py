import requests
import os
from dotenv import load_dotenv

# load API key from .env
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek/deepseek-chat",
    "messages": [
        {
            "role": "user",
            "content": "You are a farmer negotiating crop price. Buyer offered ₹16 but minimum price is ₹18. What should the farmer do?"
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

print(response.json())