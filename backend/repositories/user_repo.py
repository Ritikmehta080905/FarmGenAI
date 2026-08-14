from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.db.models.user import User
from backend.models.auth_model import SignupRequest
from backend.services.security import hash_password

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create(self, user_in: SignupRequest) -> User:
        user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.name,
            role=user_in.role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
