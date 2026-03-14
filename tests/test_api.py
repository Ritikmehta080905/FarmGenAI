import requests
import os
from dotenv import load_dotenv

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
            "content": "Farmer minimum price ₹18. Buyer offered ₹16. What should farmer do?"
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

print(response.json()["choices"][0]["message"]["content"])