import os
import json
import logging
from copy import deepcopy
from uuid import uuid4
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import select, delete, text, JSON
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
    user_id: Mapped[str] = mapped_column(nullable=True, index=True)
    buyer_name: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    min_price: Mapped[float] = mapped_column(nullable=True)
    max_price: Mapped[float] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    urgency: Mapped[str] = mapped_column(nullable=True)
    neg_mode: Mapped[str] = mapped_column(nullable=True)
    strategy: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)

class DBProduce(Base):
    __tablename__ = "produce"
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=True, index=True)
    farmer_name: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    min_price: Mapped[float] = mapped_column(nullable=True)
    shelf_life: Mapped[int] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    quality: Mapped[str] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)

class DBNegotiation(Base):
    __tablename__ = "negotiations"
    negotiation_id: Mapped[str] = mapped_column(primary_key=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    farmer_id: Mapped[str] = mapped_column(nullable=True)
    buyer_id: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(nullable=True)
    farmer_name: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    current_round: Mapped[int] = mapped_column(default=0)
    summary: Mapped[str] = mapped_column(nullable=True)
    final_price: Mapped[float] = mapped_column(nullable=True)
    transport_plan: Mapped[str] = mapped_column(nullable=True)
    peer_node: Mapped[str] = mapped_column(nullable=True)
    logs: Mapped[list] = mapped_column(type_=JSON, nullable=True)
    market_offers: Mapped[list] = mapped_column(type_=JSON, nullable=True)
    selected_buyer: Mapped[dict] = mapped_column(type_=JSON, nullable=True)
    signatures: Mapped[dict] = mapped_column(type_=JSON, nullable=True)

class DBOffer(Base):
    __tablename__ = "offers"
    id: Mapped[str] = mapped_column(primary_key=True)
    negotiation_id: Mapped[str] = mapped_column(nullable=True, index=True)
    round_num: Mapped[int] = mapped_column(default=0)
    sender: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    message: Mapped[str] = mapped_column(nullable=True)

class DBContract(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(primary_key=True)
    negotiation_id: Mapped[str] = mapped_column(nullable=True)
    farmer_id: Mapped[str] = mapped_column(nullable=True)
    buyer_id: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    final_price: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)

class DBHistory(Base):
    __tablename__ = "history"
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=True, index=True)
    negotiation_id: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    final_price: Mapped[float] = mapped_column(nullable=True)
    summary: Mapped[str] = mapped_column(nullable=True)

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
        except Exception:
            return False
    try:
        loop = asyncio.get_running_loop()
        return True
    except RuntimeError:
        return asyncio.run(_test())

db_url = settings.DATABASE_URL
if os.getenv("TESTING") == "1" or not is_postgres_running(db_url):
    db_url = "sqlite+aiosqlite:///agrinegotiator.db"
    logging.warning("⚠️ PostgreSQL not reachable or credentials invalid. Falling back to local SQLite: agrinegotiator.db")

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        try:
            from backend.db.session import Base as V1Base
            await conn.run_sync(V1Base.metadata.create_all)
        except Exception as e:
            logging.warning(f"Failed to create V1 tables: {e}")

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
    async def reset(cls):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        cls.users.clear()
        cls.farmers.clear()
        cls.buyers.clear()
        cls.produce.clear()
        cls.negotiations.clear()
        cls.offers.clear()
        cls.contracts.clear()
        cls.history.clear()



    @classmethod
    async def upsert_farmer_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        farmer_id = p.get("id") or cls.generate_id("farmer")
        p["id"] = farmer_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_farmer = await session.get(DBFarmer, farmer_id)
                if not db_farmer:
                    db_farmer = DBFarmer(id=farmer_id)
                    session.add(db_farmer)
                db_farmer.name = p.get("name")
                db_farmer.location = p.get("location")
                db_farmer.language = p.get("language")
        cls.farmers[farmer_id] = p
        return p

    @classmethod
    async def upsert_buyer_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        buyer_id = p.get("id") or cls.generate_id("buyer")
        p["id"] = buyer_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_buyer = await session.get(DBBuyer, buyer_id)
                if not db_buyer:
                    db_buyer = DBBuyer(id=buyer_id)
                    session.add(db_buyer)
                
                db_buyer.user_id = p.get("user_id")
                db_buyer.buyer_name = p.get("buyer_name")
                db_buyer.crop = p.get("crop")
                db_buyer.min_price = p.get("min_price")
                db_buyer.max_price = p.get("max_price")
                db_buyer.quantity = p.get("quantity")
                db_buyer.location = p.get("location")
                db_buyer.urgency = p.get("urgency")
                db_buyer.neg_mode = p.get("neg_mode")
                db_buyer.strategy = p.get("strategy")
                db_buyer.status = p.get("status")
        cls.buyers[buyer_id] = p
        return p

    @classmethod
    async def list_buyers_async(cls) -> list:
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(DBBuyer))
            rows = res.scalars().all()
            results = []
            for r in rows:
                results.append({
                    "id": r.id,
                    "user_id": r.user_id,
                    "buyer_name": r.buyer_name,
                    "crop": r.crop,
                    "min_price": r.min_price,
                    "max_price": r.max_price,
                    "quantity": r.quantity,
                    "location": r.location,
                    "urgency": r.urgency,
                    "neg_mode": r.neg_mode,
                    "strategy": r.strategy,
                    "status": r.status
                })
        cls.buyers = {b["id"]: b for b in results}
        return results

    @classmethod
    async def upsert_produce_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        produce_id = p.get("id") or cls.generate_id("produce")
        p["id"] = produce_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_produce = await session.get(DBProduce, produce_id)
                if not db_produce:
                    db_produce = DBProduce(id=produce_id)
                    session.add(db_produce)
                
                db_produce.user_id = p.get("user_id")
                db_produce.farmer_name = p.get("farmer_name")
                db_produce.crop = p.get("crop")
                db_produce.quantity = p.get("quantity")
                db_produce.min_price = p.get("min_price")
                db_produce.shelf_life = p.get("shelf_life")
                db_produce.location = p.get("location")
                db_produce.quality = p.get("quality")
                db_produce.language = p.get("language")
                db_produce.status = p.get("status")
        cls.produce[produce_id] = p
        return p

    @classmethod
    async def list_produce_async(cls) -> list:
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(DBProduce))
            rows = res.scalars().all()
            results = []
            for r in rows:
                results.append({
                    "id": r.id,
                    "user_id": r.user_id,
                    "farmer_name": r.farmer_name,
                    "crop": r.crop,
                    "quantity": r.quantity,
                    "min_price": r.min_price,
                    "shelf_life": r.shelf_life,
                    "location": r.location,
                    "quality": r.quality,
                    "language": r.language,
                    "status": r.status
                })
        cls.produce = {p["id"]: p for p in results}
        return results

    @classmethod
    async def create_negotiation_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        neg_id = p.get("negotiation_id") or cls.generate_id("neg")
        p["negotiation_id"] = neg_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_neg = await session.get(DBNegotiation, neg_id)
                if not db_neg:
                    db_neg = DBNegotiation(negotiation_id=neg_id)
                    session.add(db_neg)
                db_neg.crop = p.get("crop")
                db_neg.quantity = p.get("quantity")
                db_neg.farmer_id = p.get("farmer_id")
                db_neg.buyer_id = p.get("buyer_id")
                db_neg.user_id = p.get("user_id")
                db_neg.farmer_name = p.get("farmer_name")
                db_neg.status = p.get("status")
                db_neg.current_round = p.get("current_round", 0)
                db_neg.summary = p.get("summary")
                db_neg.final_price = p.get("final_price")
                tp = p.get("transport_plan")
                if isinstance(tp, dict):
                    import json
                    tp = json.dumps(tp)
                db_neg.transport_plan = tp
                db_neg.peer_node = p.get("peer_node")
                db_neg.logs = p.get("logs", [])
                db_neg.market_offers = p.get("market_offers", [])
                db_neg.selected_buyer = p.get("selected_buyer", {})
                db_neg.signatures = p.get("signatures", {})
        cls.negotiations[neg_id] = p
        return p

    @classmethod
    async def get_negotiation_async(cls, neg_id: str) -> dict:
        async with AsyncSessionLocal() as session:
            db_neg = await session.get(DBNegotiation, neg_id)
            if db_neg:
                return {
                    "negotiation_id": db_neg.negotiation_id,
                    "crop": db_neg.crop,
                    "quantity": db_neg.quantity,
                    "farmer_id": db_neg.farmer_id,
                    "buyer_id": db_neg.buyer_id,
                    "user_id": db_neg.user_id,
                    "farmer_name": db_neg.farmer_name,
                    "status": db_neg.status,
                    "current_round": db_neg.current_round,
                    "summary": db_neg.summary,
                    "final_price": db_neg.final_price,
                    "transport_plan": db_neg.transport_plan,
                    "peer_node": db_neg.peer_node,
                    "logs": db_neg.logs or [],
                    "market_offers": db_neg.market_offers or [],
                    "selected_buyer": db_neg.selected_buyer or {},
                    "signatures": db_neg.signatures or {}
                }
            return None

    @classmethod
    async def update_negotiation_async(cls, neg_id: str, payload: dict):
        payload["negotiation_id"] = neg_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_neg = await session.get(DBNegotiation, neg_id)
                if not db_neg:
                    db_neg = DBNegotiation(negotiation_id=neg_id)
                    session.add(db_neg)
                if "crop" in payload: db_neg.crop = payload["crop"]
                if "quantity" in payload: db_neg.quantity = payload["quantity"]
                if "farmer_id" in payload: db_neg.farmer_id = payload["farmer_id"]
                if "buyer_id" in payload: db_neg.buyer_id = payload["buyer_id"]
                if "user_id" in payload: db_neg.user_id = payload["user_id"]
                if "farmer_name" in payload: db_neg.farmer_name = payload["farmer_name"]
                if "status" in payload: db_neg.status = payload["status"]
                if "current_round" in payload: db_neg.current_round = payload["current_round"]
                if "summary" in payload: db_neg.summary = payload["summary"]
                if "final_price" in payload: db_neg.final_price = payload["final_price"]
                if "transport_plan" in payload: db_neg.transport_plan = payload["transport_plan"]
                if "peer_node" in payload: db_neg.peer_node = payload["peer_node"]
                if "logs" in payload: db_neg.logs = payload["logs"]
                if "market_offers" in payload: db_neg.market_offers = payload["market_offers"]
                if "selected_buyer" in payload: db_neg.selected_buyer = payload["selected_buyer"]
                if "signatures" in payload: db_neg.signatures = payload["signatures"]
        cls.negotiations[neg_id] = payload

    @classmethod
    async def append_offer_async(cls, negotiation_id: str, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("offer")
        p["negotiation_id"] = negotiation_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_offer = DBOffer(
                    id=p["id"],
                    negotiation_id=negotiation_id,
                    round_num=p.get("round", 0),
                    sender=p.get("sender"),
                    price=p.get("price"),
                    quantity=p.get("quantity"),
                    message=p.get("message")
                )
                session.add(db_offer)
        cls.offers[p["id"]] = p
        return p

    @classmethod
    async def get_offers_for_negotiation_async(cls, negotiation_id: str) -> list:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(DBOffer)
                .where(DBOffer.negotiation_id == negotiation_id)
                .order_by(DBOffer.round_num)
            )
            rows = res.scalars().all()
            return [{
                "id": r.id,
                "negotiation_id": r.negotiation_id,
                "round": r.round_num,
                "sender": r.sender,
                "price": r.price,
                "quantity": r.quantity,
                "message": r.message
            } for r in rows]

    @classmethod
    async def create_contract_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        p["id"] = cls.generate_id("contract")
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_contract = DBContract(
                    id=p["id"],
                    negotiation_id=p.get("negotiation_id"),
                    farmer_id=p.get("farmer_id"),
                    buyer_id=p.get("buyer_id"),
                    crop=p.get("crop"),
                    quantity=p.get("quantity"),
                    final_price=p.get("final_price"),
                    status=p.get("status")
                )
                session.add(db_contract)
        cls.contracts[p["id"]] = p
        return p

    @classmethod
    async def add_history_async(cls, user_id: str, entry: dict):
        record_id = cls.generate_id("hist")
        entry = deepcopy(entry)
        entry["user_id"] = user_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_history = DBHistory(
                    id=record_id,
                    user_id=user_id,
                    negotiation_id=entry.get("negotiation_id"),
                    crop=entry.get("crop"),
                    quantity=entry.get("quantity"),
                    status=entry.get("status"),
                    final_price=entry.get("final_price"),
                    summary=entry.get("summary")
                )
                session.add(db_history)
        if user_id not in cls.history:
            cls.history[user_id] = []
        cls.history[user_id].append(entry)

    @classmethod
    async def get_history_async(cls, user_id: str = "all") -> list:
        async with AsyncSessionLocal() as session:
            if user_id == "all":
                res = await session.execute(select(DBHistory).order_by(DBHistory.id.desc()).limit(50))
            else:
                res = await session.execute(select(DBHistory).where(DBHistory.user_id == user_id).order_by(DBHistory.id.desc()))
            rows = res.scalars().all()
            results = []
            for r in rows:
                results.append({
                    "negotiation_id": r.negotiation_id,
                    "crop": r.crop,
                    "quantity": r.quantity,
                    "status": r.status,
                    "final_price": r.final_price,
                    "summary": r.summary
                })
            return results
