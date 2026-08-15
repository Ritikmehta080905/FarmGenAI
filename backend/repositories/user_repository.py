import json
from copy import deepcopy
from sqlalchemy import select
from database.db import AsyncSessionLocal, DBUser

class UserRepository:
    @staticmethod
    async def get_by_id(user_id: str) -> dict | None:
        async with AsyncSessionLocal() as session:
            db_user = await session.get(DBUser, user_id)
            if not db_user:
                return None
            
            docs = []
            try: docs = json.loads(db_user.verification_docs or "[]")
            except: pass
            
            prefs = {}
            try: prefs = json.loads(db_user.preferences or "{}")
            except: pass

            return {
                "user_id": db_user.user_id,
                "name": db_user.name,
                "email": db_user.email,
                "password": db_user.password,
                "location": db_user.location,
                "language": db_user.language,
                "role": db_user.role,
                "verification_status": db_user.verification_status,
                "verification_docs": docs,
                "preferences": prefs,
                "trust_score": db_user.trust_score
            }

    @staticmethod
    async def get_by_email(email: str):
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(DBUser).where(DBUser.email == email))
            return res.scalars().first()

    @staticmethod
    async def upsert(p: dict) -> dict:
        p = deepcopy(p)
        user_id = p["user_id"]
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_user = await session.get(DBUser, user_id)
                if not db_user:
                    db_user = DBUser(user_id=user_id)
                    session.add(db_user)
                
                if "name" in p: db_user.name = p["name"]
                if "email" in p: db_user.email = p["email"]
                if p.get("password"): db_user.password = p["password"]
                if "location" in p: db_user.location = p["location"]
                if "language" in p: db_user.language = p["language"]
                if "role" in p: db_user.role = p["role"]
                if "verification_status" in p: db_user.verification_status = p["verification_status"]
                if "verification_docs" in p: db_user.verification_docs = json.dumps(p["verification_docs"])
                if "preferences" in p: db_user.preferences = json.dumps(p["preferences"])
                if "trust_score" in p: db_user.trust_score = p["trust_score"]
        return p

