import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

URL = "https://openrouter.ai/api/v1/chat/completions"


def ask_llm(prompt):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat-v3",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(URL, headers=headers, json=data)

    result = response.json()

    return result["choices"][0]["message"]["content"]