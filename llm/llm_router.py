from llm.openrouter_client import ask_llm as ask_openrouter
from llm.groq_client import ask_groq

def ask_llm(prompt, provider="openrouter"):
    if provider == "groq":
        return ask_groq(prompt)
    else:
        return ask_openrouter(prompt)
