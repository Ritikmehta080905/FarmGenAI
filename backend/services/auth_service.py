import sqlite3
from database.db import Database, _conn


def signup_user(data: dict):
    # ── Robust Email Check ─────────────────────────────
    with _conn() as c:
        row = c.execute("SELECT user_id FROM users WHERE email=?", (data["email"],)).fetchone()
        if row:
            return {"error": "User with this email already exists"}

    user_id = Database.generate_id("user")
    role = data.get("role", "farmer").lower()

    user_record = {
        "user_id": user_id,
        "name": data["name"],
        "email": data["email"],
        "password": data["password"],
        "location": data["location"],
        "language": data.get("language", "English"),
        "role": role,
        "verification_status": "PENDING",
        "preferences": {},
        "trust_score": 4.0
    }

    # Persist to Core User Table
    Database.upsert_user(user_record)

    # ── Role-Specific Initialization ───────────────────
    if role == "farmer":
        Database.upsert_farmer({
            "id": user_id,
            "name": data["name"],
            "location": data["location"],
            "language": user_record["language"]
        })
    elif role == "buyer":
        Database.upsert_buyer({
            "id": user_id,
            "name": data["name"],
            "location": data["location"],
            "budget": 100000, # Default high budget for new buyers
            "max_quantity": 5000,
            "target_price": 20,
            "strategy": "Direct procurement",
            "preferences": {}
        })
    
    Database.add_history(user_id, {"type": "ACCOUNT_CREATED", "role": role, "message": f"New {role} account initialized."})

    return {
        "user_id": user_id,
        "name": user_record["name"],
        "email": user_record["email"],
        "location": user_record["location"],
        "language": user_record["language"],
        "role": role,
        "trust_score": 4.0,
        "message": "Signup successful"
    }


def login_user(data: dict):
    # Check Database for most fresh user data
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=? AND password=?", 
                       (data["email"], data["password"])).fetchone()
        if row:
            u = dict(row)
            return {
                "user_id": u["user_id"],
                "name": u["name"],
                "email": u["email"],
                "location": u["location"],
                "language": u["language"],
                "role": u.get("role"),
                "trust_score": u.get("trust_score", 4.0),
                "message": "Login successful"
            }

    return {"error": "Invalid email or password"}