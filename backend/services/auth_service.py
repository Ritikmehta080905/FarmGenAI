from database.db import Database, DBUser, AsyncSessionLocal
from sqlalchemy import select
from backend.services.security import hash_password, verify_password, create_access_token

async def signup_user(data: dict):
    # Ensure a unique email using phone or name if default email is passed
    email = data.get("email")
    phone = data.get("phone", "")
    if not email or email == "user@agri.com":
        clean_phone = "".join(filter(str.isalnum, phone)) or Database.generate_id("u")
        email = f"{clean_phone}@agri.com"
        data["email"] = email

    # ── Robust Email Check ─────────────────────────────
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(DBUser).where(DBUser.email == email))
        existing = res.scalars().first()
            
    if existing:
        token = create_access_token({"sub": existing.user_id, "role": existing.role})
        return {
            "user_id": existing.user_id,
            "name": existing.name,
            "email": existing.email,
            "location": existing.location,
            "language": existing.language,
            "role": existing.role,
            "trust_score": existing.trust_score,
            "token": token,
            "message": "Signup successful (existing user retrieved)"
        }

    user_id = Database.generate_id("user")
    role = data.get("role", "farmer").lower()

    # Hash password securely using Bcrypt
    hashed_pwd = hash_password(data["password"])

    user_record = {
        "user_id": user_id,
        "name": data["name"],
        "email": email,
        "password": hashed_pwd,
        "location": data.get("location", "Pune"),
        "language": data.get("language", "English"),
        "role": role,
        "verification_status": "PENDING",
        "preferences": {},
        "trust_score": 4.0
    }

    # Persist to Core User Table
    from backend.repositories.user_repository import UserRepository
    await UserRepository.upsert(user_record)
    Database.users[user_id] = user_record

    # ── Role-Specific Initialization ───────────────────
    if role == "farmer":
        await Database.upsert_farmer_async({
            "id": user_id,
            "name": data["name"],
            "location": user_record["location"],
            "language": user_record["language"]
        })
    elif role == "buyer":
        await Database.upsert_buyer_async({
            "id": user_id,
            "name": data["name"],
            "location": user_record["location"],
            "budget": 100000, # Default high budget for new buyers
            "max_quantity": 5000,
            "target_price": 20,
            "strategy": "Direct procurement",
            "preferences": {}
        })
    
    await Database.add_history_async(user_id, {"type": "ACCOUNT_CREATED", "role": role, "message": f"New {role} account initialized."})

    # Issue access token
    token = create_access_token({"sub": user_id, "role": role})

    return {
        "user_id": user_id,
        "name": user_record["name"],
        "email": user_record["email"],
        "location": user_record["location"],
        "language": user_record["language"],
        "role": role,
        "trust_score": 4.0,
        "token": token,
        "message": "Signup successful"
    }


async def login_user(data: dict):
    identifier = data.get("email") or data.get("phone") or ""
    clean_id = "".join(filter(str.isalnum, identifier))

    # Check Database for most fresh user data
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(DBUser).where(
                (DBUser.email == identifier) | 
                (DBUser.email == f"{clean_id}@agri.com") |
                (DBUser.name == identifier)
            )
        )
        u = res.scalars().first()

    if u:
        if not verify_password(data.get("password", ""), u.password):
            return {"error": "Invalid email or password"}
        token = create_access_token({"sub": u.user_id, "role": u.role})
        return {
            "user_id": u.user_id,
            "name": u.name,
            "email": u.email,
            "location": u.location,
            "language": u.language,
            "role": u.role,
            "trust_score": u.trust_score,
            "token": token,
            "message": "Login successful"
        }

    # Auto-register new user seamlessly so real JWT is generated in Postgres
    role = "farmer"
    lower_id = identifier.lower()
    for r in ["admin", "buyer", "warehouse", "transport", "processor"]:
        if r in lower_id:
            role = r
            break

    name = identifier.split("@")[0].capitalize() if "@" in identifier else identifier
    new_user = await signup_user({
        "name": name or "User",
        "email": identifier if "@" in identifier else f"{clean_id}@agri.com",
        "phone": identifier if not "@" in identifier else "",
        "password": data.get("password", "1234"),
        "role": role
    })
    return new_user