#!/usr/bin/env python3
"""
Debug script to inspect raw LLM responses
"""

import os
os.environ["DEBUG_LLM"] = "true"

from llm.negotiation_reasoning import farmer_decision

print("=== Raw LLM Response Debug ===")
print("Testing farmer decision with offer below minimum...")

result = farmer_decision(18, 15, 3)
print(f"Parsed Result: {result}")