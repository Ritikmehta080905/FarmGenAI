"""Quick integration check for the three new features."""
import agents.buyer_agent as bm
import agents.farmer_agent as fm
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.negotiation_service import service
from database.db import Database

bm.llm_client = None
fm.llm_client = None
Database.reset()
service.active_negotiations.clear()
service._ensure_default_buyers()

client = TestClient(app)

payload = {
    "farmer_name": "Ramesh",
    "crop": "Onion",
    "quantity": 800,
    "min_price": 20,
    "shelf_life": 5,
    "location": "Nashik",
    "quality": "A",
    "language": "Marathi",
}

# 1. POST returns RUNNING immediately
r = client.post("/start-negotiation", json=payload)
assert r.status_code == 200
initial = r.json()
print("[1] Immediate response status:", initial["status"])
assert initial["status"] == "RUNNING", f"expected RUNNING, got {initial['status']}"

# 2. Poll for final result
neg_id = initial["negotiation_id"]
status = client.get(f"/negotiation-status/{neg_id}").json()
print("[2] Polled final status:", status["status"])
assert status["status"] != "RUNNING"

# 3. Multiple buyer offers present
offers = status.get("market_offers", [])
print("[3] market_offers count:", len(offers))
assert len(offers) >= 3

# 4. Selected buyer set
buyer = status.get("selected_buyer") or {}
print("[4] selected_buyer:", buyer.get("buyer_name"))
assert buyer.get("buyer_name")

# 5. Logs present
logs = status.get("logs", [])
print("[5] logs count:", len(logs))
assert len(logs) > 0

# 6. History saved
hist_resp = client.get("/api/history/all")
print("[6] /api/history/all status:", hist_resp.status_code)
assert hist_resp.status_code == 200
hist_data = hist_resp.json()
print("[6] history items:", len(hist_data.get("history", [])))
assert len(hist_data.get("history", [])) >= 1

# 7. Negotiations list endpoint
negs_resp = client.get("/api/negotiations")
assert negs_resp.status_code == 200
negs = negs_resp.json().get("negotiations", [])
print("[7] /api/negotiations count:", len(negs))
assert len(negs) >= 1

# 8. Negotiation row has created_at timestamp
assert negs[0].get("created_at"), "no created_at in negotiation row"
print("[8] created_at:", negs[0]["created_at"])

print("\n✅  All integration checks passed!")
