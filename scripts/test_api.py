import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("====================================")
    print("🔍 FarmGenAI Full System Audit 🔍")
    print("====================================\n")

    # 1. Check API Health
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"[API Root] ✅ OK - Status {r.status_code}")
    except Exception as e:
        print(f"[API Root] ❌ FAILED - {e}")

    # 2. Check Node Hub (P2P)
    try:
        r = requests.get(f"{BASE_URL}/api/nodes")
        if r.status_code == 200:
            nodes = r.json().get("nodes", [])
            print(f"[P2P Network] ✅ OK - {len(nodes)} nodes connected")
        else:
            print(f"[P2P Network] ❌ FAILED - Status {r.status_code}")
    except Exception as e:
        print(f"[P2P Network] ❌ FAILED - {e}")

    # 3. Check Negotiation Engine (Full Supply Chain)
    try:
        print("[Negotiation Engine] Testing full supply chain AI pipeline... (This might take a few seconds)")
        payload = {
            "scenario": "direct-sale",
            "user_id": "audit_user",
            "farmer_name": "Audit Farmer",
            "crop": "Tomato",
            "quantity": 100,
            "min_price": 20,
            "location": "Nashik"
        }
        r = requests.post(f"{BASE_URL}/start-negotiation", json=payload, timeout=25)
        if r.status_code == 200:
            data = r.json()
            print(f"[Negotiation Engine] ✅ OK - Status {data.get('status')} - Deal reached or fallback executed.")
        else:
            print(f"[Negotiation Engine] ❌ FAILED - Status {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[Negotiation Engine] ❌ FAILED - {e}")

    # 4. Check List Agents
    try:
        r = requests.get(f"{BASE_URL}/api/agents")
        if r.status_code == 200:
            print(f"[Agent Directory] ✅ OK - Returned {len(r.json())} agent types.")
        else:
            print(f"[Agent Directory] ❌ FAILED - Status {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[Agent Directory] ❌ FAILED - {e}")

if __name__ == "__main__":
    test_endpoints()
