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

class DBBuyerRequirement(Base):
    __tablename__ = "buyer_requirements"
    requirement_id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=True, index=True)
    buyer_name: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(nullable=False)
    target_price: Mapped[float] = mapped_column(nullable=False)
    max_price: Mapped[float] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=False)
    budget: Mapped[float] = mapped_column(nullable=False)
    delivery_days: Mapped[int] = mapped_column(default=7)
    quality_grade: Mapped[str] = mapped_column(default="A")
    notes: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(default="ACTIVE", index=True)
    created_at: Mapped[str] = mapped_column(nullable=True)

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
    data: Mapped[str] = mapped_column(nullable=True)
    negotiation_id: Mapped[str] = mapped_column(nullable=True)
    crop: Mapped[str] = mapped_column(nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    final_price: Mapped[float] = mapped_column(nullable=True)
    summary: Mapped[str] = mapped_column(nullable=True)

class DBMspPrice(Base):
    __tablename__ = "msp_prices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    crop: Mapped[str] = mapped_column(nullable=False, index=True)
    crop_full_name: Mapped[str] = mapped_column(nullable=True)
    group: Mapped[str] = mapped_column(nullable=True)
    year: Mapped[str] = mapped_column(nullable=False)
    msp_price_per_quintal: Mapped[float] = mapped_column(nullable=False)

class DBMarketMapping(Base):
    __tablename__ = "market_mappings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    district: Mapped[str] = mapped_column(nullable=False, index=True)
    market_name: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)

class DBCropQualityReference(Base):
    __tablename__ = "crop_quality_references"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    crop: Mapped[str] = mapped_column(nullable=False, index=True)
    variety: Mapped[str] = mapped_column(nullable=False)
    grade: Mapped[str] = mapped_column(nullable=False)
    min_size_mm: Mapped[float] = mapped_column(nullable=True)
    max_moisture_pct: Mapped[float] = mapped_column(nullable=True)
    color_standards: Mapped[str] = mapped_column(nullable=True)
    skin_firmness: Mapped[str] = mapped_column(nullable=True)
    common_defects_allowed: Mapped[str] = mapped_column(nullable=True)

class DBWarehouse(Base):
    __tablename__ = "warehouses"
    warehouse_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    district: Mapped[str] = mapped_column(nullable=False, index=True)
    location: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    capacity_mt: Mapped[float] = mapped_column(nullable=False)
    available_capacity_mt: Mapped[float] = mapped_column(nullable=False)
    price_per_mt_per_day: Mapped[float] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(nullable=True)
    contact_number: Mapped[str] = mapped_column(nullable=True)

class DBTransporter(Base):
    __tablename__ = "transporters"
    transporter_id: Mapped[str] = mapped_column(primary_key=True)
    provider_name: Mapped[str] = mapped_column(nullable=False)
    vehicle_type: Mapped[str] = mapped_column(nullable=False)
    capacity_mt: Mapped[float] = mapped_column(nullable=False)
    rate_per_km: Mapped[float] = mapped_column(nullable=False)
    base_fare: Mapped[float] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(nullable=True)
    contact_number: Mapped[str] = mapped_column(nullable=True)
    current_location: Mapped[str] = mapped_column(nullable=True)

class DBTrustScore(Base):
    __tablename__ = "trust_scores"
    user_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    average_rating: Mapped[float] = mapped_column(nullable=False, default=4.0)
    fulfillment_rate: Mapped[float] = mapped_column(nullable=False, default=100.0)
    payment_punctuality: Mapped[float] = mapped_column(nullable=False, default=100.0)
    total_completed_deals: Mapped[int] = mapped_column(nullable=False, default=0)
    contract_breaches: Mapped[int] = mapped_column(nullable=False, default=0)
    trust_score_final: Mapped[float] = mapped_column(nullable=False, default=4.0)

class DBSeasonalCalendar(Base):
    __tablename__ = "seasonal_calendar"
    season_id: Mapped[str] = mapped_column(primary_key=True)
    event_name: Mapped[str] = mapped_column(nullable=False)
    month_range: Mapped[str] = mapped_column(nullable=False)
    affected_crops: Mapped[str] = mapped_column(nullable=False)
    price_impact_trend: Mapped[str] = mapped_column(nullable=False)
    market_behavior_description: Mapped[str] = mapped_column(nullable=True)

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
    requirements: dict = {}
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
    async def upsert_user_async(cls, payload: dict) -> dict:
        from backend.repositories.user_repository import UserRepository
        user = await UserRepository.upsert(payload)
        user_id = user.get("user_id")
        if user_id:
            cls.users[user_id] = user
        return user

    @classmethod
    def upsert_user(cls, payload: dict) -> dict:
        user_id = payload.get("user_id")
        if user_id:
            cls.users[user_id] = payload
        return payload

    @classmethod
    async def get_user_async(cls, user_id: str) -> dict | None:
        from backend.repositories.user_repository import UserRepository
        user = await UserRepository.get_by_id(user_id)
        if user:
            cls.users[user_id] = user
            return user
        return cls.users.get(user_id)

    @classmethod
    def get_user(cls, user_id: str) -> dict | None:
        return cls.users.get(user_id)

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
    async def upsert_requirement_async(cls, payload: dict) -> dict:
        p = deepcopy(payload)
        req_id = p.get("requirement_id") or cls.generate_id("req")
        p["requirement_id"] = req_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_req = await session.get(DBBuyerRequirement, req_id)
                if not db_req:
                    db_req = DBBuyerRequirement(requirement_id=req_id)
                    session.add(db_req)
                
                db_req.user_id = p.get("user_id")
                db_req.buyer_name = p.get("buyer_name")
                db_req.crop = p.get("crop")
                db_req.quantity = float(p.get("quantity", 0))
                db_req.target_price = float(p.get("target_price", 0))
                db_req.max_price = float(p["max_price"]) if p.get("max_price") is not None else None
                db_req.location = p.get("location")
                db_req.budget = float(p.get("budget", 0))
                db_req.delivery_days = int(p.get("delivery_days", 7))
                db_req.quality_grade = p.get("quality_grade", "A")
                db_req.notes = p.get("notes", "")
                db_req.status = p.get("status", "ACTIVE")
                db_req.created_at = p.get("created_at")
        cls.requirements[req_id] = p
        return p

    @classmethod
    async def get_requirement_async(cls, req_id: str) -> dict | None:
        async with AsyncSessionLocal() as session:
            db_req = await session.get(DBBuyerRequirement, req_id)
            if db_req:
                data = {
                    "requirement_id": db_req.requirement_id,
                    "user_id": db_req.user_id,
                    "buyer_name": db_req.buyer_name,
                    "crop": db_req.crop,
                    "quantity": db_req.quantity,
                    "target_price": db_req.target_price,
                    "max_price": db_req.max_price,
                    "location": db_req.location,
                    "budget": db_req.budget,
                    "delivery_days": db_req.delivery_days,
                    "quality_grade": db_req.quality_grade,
                    "notes": db_req.notes,
                    "status": db_req.status,
                    "created_at": db_req.created_at,
                }
                cls.requirements[req_id] = data
                return data
        return cls.requirements.get(req_id)

    @classmethod
    async def list_requirements_async(cls, crop: str = None, location: str = None, status: str = None) -> list:
        async with AsyncSessionLocal() as session:
            stmt = select(DBBuyerRequirement)
            if status:
                stmt = stmt.where(DBBuyerRequirement.status == status)
            if crop:
                stmt = stmt.where(DBBuyerRequirement.crop.ilike(crop))
            if location:
                stmt = stmt.where(DBBuyerRequirement.location.ilike(location))
            res = await session.execute(stmt)
            rows = res.scalars().all()
            results = [
                {
                    "requirement_id": r.requirement_id,
                    "user_id": r.user_id,
                    "buyer_name": r.buyer_name,
                    "crop": r.crop,
                    "quantity": r.quantity,
                    "target_price": r.target_price,
                    "max_price": r.max_price,
                    "location": r.location,
                    "budget": r.budget,
                    "delivery_days": r.delivery_days,
                    "quality_grade": r.quality_grade,
                    "notes": r.notes,
                    "status": r.status,
                    "created_at": r.created_at,
                }
                for r in rows
            ]
            cls.requirements = {r["requirement_id"]: r for r in results}
            return results

    @classmethod
    async def update_requirement_async(cls, req_id: str, updates: dict) -> dict | None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_req = await session.get(DBBuyerRequirement, req_id)
                if not db_req:
                    return None
                for k, v in updates.items():
                    if hasattr(db_req, k) and v is not None:
                        setattr(db_req, k, v)
        return await cls.get_requirement_async(req_id)

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
                    data=json.dumps(entry) if entry else None,
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
    def get_history(cls, user_id: str = "all") -> list:
        async def _get():
            return await cls.get_history_async(user_id)
        return _run_async(_get())

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
                if r.negotiation_id:
                    results.append({
                        "negotiation_id": r.negotiation_id,
                        "crop": r.crop,
                        "quantity": r.quantity,
                        "status": r.status,
                        "final_price": r.final_price,
                        "summary": r.summary
                    })
                elif r.data:
                    try:
                        data_dict = json.loads(r.data)
                        if isinstance(data_dict, dict) and data_dict.get("type") and data_dict.get("type") != "ACCOUNT_CREATED":
                            results.append(data_dict)
                    except Exception:
                        pass
            return results

    @classmethod
    def get_msp_price(cls, crop: str) -> float | None:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBMspPrice).where(DBMspPrice.crop.ilike(crop))
                res = await session.execute(stmt)
                row = res.scalars().first()
                return row.msp_price_per_quintal if row else None
        try:
            return _run_async(_get())
        except Exception:
            return None

    @classmethod
    def get_market_mappings(cls, district: str) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBMarketMapping).where(DBMarketMapping.district.ilike(district))
                res = await session.execute(stmt)
                rows = res.scalars().all()
                return [{"district": r.district, "market_name": r.market_name, "state": r.state} for r in rows]
        try:
            return _run_async(_get())
        except Exception:
            return []

    @classmethod
    def get_crop_quality_reference(cls, crop: str) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBCropQualityReference).where(DBCropQualityReference.crop.ilike(crop))
                res = await session.execute(stmt)
                rows = res.scalars().all()
                return [{
                    "crop": r.crop,
                    "variety": r.variety,
                    "grade": r.grade,
                    "min_size_mm": r.min_size_mm,
                    "max_moisture_pct": r.max_moisture_pct,
                    "color_standards": r.color_standards,
                    "skin_firmness": r.skin_firmness,
                    "common_defects_allowed": r.common_defects_allowed
                } for r in rows]
        try:
            return _run_async(_get())
        except Exception:
            return []

    @classmethod
    def get_seasonal_calendar(cls) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBSeasonalCalendar)
                res = await session.execute(stmt)
                rows = res.scalars().all()
                return [{
                    "season_id": r.season_id,
                    "event_name": r.event_name,
                    "month_range": r.month_range,
                    "affected_crops": r.affected_crops,
                    "price_impact_trend": r.price_impact_trend,
                    "market_behavior_description": r.market_behavior_description
                } for r in rows]
        try:
            return _run_async(_get())
        except Exception:
            return []

    @classmethod
    def get_trust_score(cls, user_id: str) -> dict | None:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBTrustScore).where(DBTrustScore.user_id == user_id)
                res = await session.execute(stmt)
                r = res.scalars().first()
                if not r:
                    return None
                return {
                    "user_id": r.user_id,
                    "name": r.name,
                    "role": r.role,
                    "average_rating": r.average_rating,
                    "fulfillment_rate": r.fulfillment_rate,
                    "payment_punctuality": r.payment_punctuality,
                    "total_completed_deals": r.total_completed_deals,
                    "contract_breaches": r.contract_breaches,
                    "trust_score_final": r.trust_score_final
                }
        try:
            return _run_async(_get())
        except Exception:
            return None

    @classmethod
    def get_warehouse_list(cls, district: str) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBWarehouse).where(DBWarehouse.district.ilike(district))
                res = await session.execute(stmt)
                rows = res.scalars().all()
                return [{
                    "warehouse_id": r.warehouse_id,
                    "name": r.name,
                    "district": r.district,
                    "location": r.location,
                    "type": r.type,
                    "capacity_mt": r.capacity_mt,
                    "available_capacity_mt": r.available_capacity_mt,
                    "price_per_mt_per_day": r.price_per_mt_per_day,
                    "rating": r.rating,
                    "contact_number": r.contact_number
                } for r in rows]
        try:
            return _run_async(_get())
        except Exception:
            return []

    @classmethod
    def get_transporter_list(cls, current_location: str) -> list:
        async def _get():
            async with AsyncSessionLocal() as session:
                stmt = select(DBTransporter).where(DBTransporter.current_location.ilike(current_location))
                res = await session.execute(stmt)
                rows = res.scalars().all()
                return [{
                    "transporter_id": r.transporter_id,
                    "provider_name": r.provider_name,
                    "vehicle_type": r.vehicle_type,
                    "capacity_mt": r.capacity_mt,
                    "rate_per_km": r.rate_per_km,
                    "base_fare": r.base_fare,
                    "rating": r.rating,
                    "contact_number": r.contact_number,
                    "current_location": r.current_location
                } for r in rows]
        try:
            return _run_async(_get())
        except Exception:
            return []
