import os
import json
import logging
from copy import deepcopy
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import select, delete
from config.settings import settings

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True, index=True)
    password: Mapped[str] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=True)
    verification_status: Mapped[str] = mapped_column(default="PENDING")
    verification_docs: Mapped[str] = mapped_column(default="[]")
    preferences: Mapped[str] = mapped_column(default="{}")
    trust_score: Mapped[float] = mapped_column(default=4.0)

class DBFarmer(Base):
    __tablename__ = "farmers"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(nullable=True)

class DBBuyer(Base):
    __tablename__ = "buyers"
    id: Mapped[str] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()

class DBProduce(Base):
    __tablename__ = "produce"
    id: Mapped[str] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()

class DBNegotiation(Base):
    __tablename__ = "negotiations"
    negotiation_id: Mapped[str] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()

class DBOffer(Base):
    __tablename__ = "offers"
    id: Mapped[str] = mapped_column(primary_key=True)
    negotiation_id: Mapped[str] = mapped_column(nullable=True, index=True)
    round_num: Mapped[int] = mapped_column(default=0)
    data: Mapped[str] = mapped_column()

class DBContract(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()

class DBHistory(Base):
    __tablename__ = "history"
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=True, index=True)
    data: Mapped[str] = mapped_column()

# Engine setup
from sqlalchemy import text

def _run_async(coro):
    import asyncio
    import threading
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        res_list = []
        exc_list = []
        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                res = new_loop.run_until_complete(coro)
                res_list.append(res)
                new_loop.close()
            except Exception as e:
                exc_list.append(e)
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        if exc_list:
            raise exc_list[0]
        return res_list[0]
    else:
        return asyncio.run(coro)

def is_postgres_running(url: str) -> bool:
    if "postgres" not in url.lower():
        return False
    async def _test():
        try:
            temp_engine = create_async_engine(url, echo=False)
            async with temp_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await temp_engine.dispose()
            return True
        except:
            return False
    try:
        return _run_async(_test())
    except:
        return False

db_url = settings.DATABASE_URL
if os.getenv("TESTING") == "1" or not is_postgres_running(db_url):
    db_url = "sqlite+aiosqlite:///agrinegotiator.db"
    logging.warning("⚠️ PostgreSQL not reachable or credentials invalid. Falling back to local SQLite: agrinegotiator.db")

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default admin and farmer if users table is empty
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(DBUser).limit(1))
            if not res.scalars().first():
                from backend.services.security import hash_password
                admin = DBUser(
                    user_id="admin_001",
                    name="Platform Administrator",
                    email="admin@agri.ai",
                    password=hash_password("password123"),
                    location="Pune, MH",
                    language="English",
                    trust_score=5.0,
                    role="admin",
                    verification_status="VERIFIED"
                )
                farmer = DBUser(
                    user_id="farmer_001",
                    name="Pradeep Patel",
                    email="pradeep@farm.ai",
                    password=hash_password("password123"),
                    location="Nashik, MH",
                    language="Marathi",
                    trust_score=4.5,
                    role="farmer",
                    verification_status="VERIFIED"
                )
                db_farmer = DBFarmer(
                    id="farmer_001",
                    name="Pradeep Patel",
                    location="Nashik, MH",
                    language="Marathi"
                )
                session.add_all([admin, farmer, db_farmer])

class Database:
    users: dict = {}
    farmers: dict = {}
    buyers: dict = {}
    produce: dict = {}
    negotiations: dict = {}
    offers: dict = {}
    contracts: dict = {}
    history: dict = {}

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:8]}"

    @classmethod
    def reset(cls):
        async def _reset():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        _run_async(_reset())
        cls.users.clear()
        cls.farmers.clear()
        cls.buyers.clear()
        cls.produce.clear()
        cls.negotiations.clear()
        cls.offers.clear()
        cls.contracts.clear()
        cls.history.clear()

    @classmethod
    def upsert_user(cls, p: dict) -> dict:
        p = deepcopy(p)
        async def _upsert():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    user_id = p["user_id"]
                    db_user = await session.get(DBUser, user_id)
                    if not db_user:
                        db_user = DBUser(user_id=user_id)
                        session.add(db_user)
                    
                    db_user.name = p.get("name")
                    db_user.email = p.get("email")
                    if p.get("password"):
                        db_user.password = p.get("password")
                    db_user.location = p.get("location")
                    db_user.language = p.get("language")
                    db_user.role = p.get("role")
                    db_user.verification_status = p.get("verification_status", "PENDING")
                    db_user.verification_docs = json.dumps(p.get("verification_docs", []))
                    db_user.preferences = json.dumps(p.get("preferences", {}))
                    db_user.trust_score = p.get("trust_score", 4.0)
        _run_async(_upsert())
        cls.users[p["user_id"]] = p
        return p

    @classmethod
    def get_user(cls, user_id: str) -> dict:
        async def _get():
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
        d = _run_async(_get())
        if d:
            cls.users[user_id] = d
        return d

    @classmethod
    def upsert_farmer(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        farmer_id = p.get("id") or cls.generate_id("farmer")
        p["id"] = farmer_id
        async def _upsert():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_farmer = await session.get(DBFarmer, farmer_id)
                    if not db_farmer:
                        db_farmer = DBFarmer(id=farmer_id)
                        session.add(db_farmer)
                    db_farmer.name = p.get("name")
                    db_farmer.location = p.get("location")
                    db_farmer.language = p.get("language")
        _run_async(_upsert())
        cls.farmers[farmer_id] = p
        return p

    @classmethod
    def upsert_buyer(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        buyer_id = p.get("id") or cls.generate_id("buyer")
        p["id"] = buyer_id
        async def _upsert():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_buyer = await session.get(DBBuyer, buyer_id)
                    if not db_buyer:
                        db_buyer = DBBuyer(id=buyer_id)
                        session.add(db_buyer)
                    db_buyer.data = json.dumps(p)
        _run_async(_upsert())
        cls.buyers[buyer_id] = p
        return p

    @classmethod
    def list_buyers(cls) -> list:
        async def _list():
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(DBBuyer))
                rows = res.scalars().all()
                return [json.loads(r.data) for r in rows]
        results = _run_async(_list())
        cls.buyers = {b["id"]: b for b in results}
        return results

    @classmethod
    def create_produce(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("produce")
        async def _create():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_produce = DBProduce(id=p["id"], data=json.dumps(p))
                    session.add(db_produce)
        _run_async(_create())
        cls.produce[p["id"]] = p
        return p

    @classmethod
    def list_produce(cls) -> list:
        async def _list():
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(DBProduce))
                rows = res.scalars().all()
                return [json.loads(r.data) for r in rows]
        results = _run_async(_list())
        cls.produce = {p["id"]: p for p in results}
        return results

    @classmethod
    def create_negotiation(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        neg_id = p.get("negotiation_id") or cls.generate_id("neg")
        p["negotiation_id"] = neg_id
        async def _create():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_neg = await session.get(DBNegotiation, neg_id)
                    if not db_neg:
                        db_neg = DBNegotiation(negotiation_id=neg_id)
                        session.add(db_neg)
                    db_neg.data = json.dumps(p)
        _run_async(_create())
        cls.negotiations[neg_id] = p
        return p

    @classmethod
    def get_negotiation(cls, neg_id: str) -> dict:
        async def _get():
            async with AsyncSessionLocal() as session:
                db_neg = await session.get(DBNegotiation, neg_id)
                if db_neg:
                    return json.loads(db_neg.data)
                return None
        p = _run_async(_get())
        if p:
            cls.negotiations[neg_id] = p
        return p

    @classmethod
    def update_negotiation(cls, neg_id: str, payload: dict):
        payload["negotiation_id"] = neg_id
        async def _update():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_neg = await session.get(DBNegotiation, neg_id)
                    if not db_neg:
                        db_neg = DBNegotiation(negotiation_id=neg_id)
                        session.add(db_neg)
                    db_neg.data = json.dumps(payload)
        _run_async(_update())
        cls.negotiations[neg_id] = payload

    @classmethod
    def append_offer(cls, negotiation_id: str, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("offer")
        p["negotiation_id"] = negotiation_id
        async def _append():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_offer = DBOffer(
                        id=p["id"],
                        negotiation_id=negotiation_id,
                        round_num=p.get("round", 0),
                        data=json.dumps(p)
                    )
                    session.add(db_offer)
        _run_async(_append())
        cls.offers[p["id"]] = p
        return p

    @classmethod
    def get_offers_for_negotiation(cls, negotiation_id: str) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(DBOffer)
                    .where(DBOffer.negotiation_id == negotiation_id)
                    .order_by(DBOffer.round_num)
                )
                rows = res.scalars().all()
                return [json.loads(r.data) for r in rows]
        return _run_async(_get())

    @classmethod
    def create_contract(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("contract")
        async def _create():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_contract = DBContract(id=p["id"], data=json.dumps(p))
                    session.add(db_contract)
        _run_async(_create())
        cls.contracts[p["id"]] = p
        return p

    @classmethod
    def add_history(cls, user_id: str, entry: dict):
        record_id = cls.generate_id("hist")
        entry = deepcopy(entry)
        entry["user_id"] = user_id
        async def _add():
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_history = DBHistory(
                        id=record_id,
                        user_id=user_id,
                        data=json.dumps(entry)
                    )
                    session.add(db_history)
        _run_async(_add())
        if user_id not in cls.history:
            cls.history[user_id] = []
        cls.history[user_id].append(entry)

    @classmethod
    def get_history(cls, user_id: str = "all") -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                if user_id == "all":
                    res = await session.execute(select(DBHistory).order_by(DBHistory.id.desc()).limit(50))
                else:
                    res = await session.execute(select(DBHistory).where(DBHistory.user_id == user_id).order_by(DBHistory.id.desc()))
                rows = res.scalars().all()
                return [json.loads(r.data) for r in rows]
        return _run_async(_get())
