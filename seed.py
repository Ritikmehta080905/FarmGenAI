import asyncio
from backend.db.session import AsyncSessionLocal
from backend.db.models.user import User
from backend.services.security import hash_password

async def seed_db():
    async with AsyncSessionLocal() as session:
        user = User(
            email="pradeep@farm.ai",
            hashed_password=hash_password("password123"),
            full_name="Pradeep Kumar",
            role="farmer",
            is_active=True
        )
        buyer = User(
            email="buyer@farm.ai",
            hashed_password=hash_password("password123"),
            full_name="BigBasket Procurement",
            role="buyer",
            is_active=True
        )
        session.add(user)
        session.add(buyer)
        await session.commit()
        print("Database seeded with test accounts!")

if __name__ == "__main__":
    asyncio.run(seed_db())
