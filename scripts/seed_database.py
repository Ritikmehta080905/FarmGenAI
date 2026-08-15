import asyncio
import json
import random
from faker import Faker
from database.db import (
    engine,
    Base,
    AsyncSessionLocal,
    DBFarmer,
    DBBuyer,
    DBWarehouse,
    DBTransporter,
    DBProduce,
    DBNegotiation,
    DBProcessor,
    DBCompost
)
from backend.services.rag_service import rag_service

fake = Faker('en_IN')

MAHARASHTRA_DISTRICTS = ["Nashik", "Pune", "Jalgaon", "Sangli", "Solapur", "Nagpur", "Amravati", "Kolhapur", "Aurangabad", "Ahmednagar"]
CROPS = ["Tomato", "Onion", "Grapes", "Sugarcane", "Soybean", "Cotton", "Banana", "Pomegranate", "Turmeric", "Maize"]

async def seed_db():
    print("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Seed Farmers (300)
            print("Seeding Farmers...")
            farmers = []
            for i in range(300):
                f = DBFarmer(
                    id=f"F_{i:04d}",
                    name=fake.name(),
                    location=random.choice(MAHARASHTRA_DISTRICTS),
                    language="Marathi"
                )
                farmers.append(f)
                session.add(f)

            # 2. Seed Buyers (100)
            print("Seeding Buyers...")
            buyers = []
            for i in range(100):
                b = DBBuyer(
                    id=f"B_{i:04d}",
                    user_id=f"U_{i:04d}",
                    buyer_name=fake.company(),
                    crop=random.choice(CROPS),
                    min_price=random.uniform(15, 30),
                    max_price=random.uniform(35, 60),
                    quantity=random.uniform(500, 5000),
                    location=random.choice(MAHARASHTRA_DISTRICTS),
                    urgency="Normal",
                    neg_mode="auto",
                    strategy="Value Buyer",
                    status="Active"
                )
                buyers.append(b)
                session.add(b)

            # 3. Seed Warehouses (30)
            print("Seeding Warehouses...")
            warehouses = []
            for i in range(30):
                w = DBWarehouse(
                    warehouse_id=f"WH_{i:03d}",
                    name=f"{fake.company()} Storage",
                    district=random.choice(MAHARASHTRA_DISTRICTS),
                    location="City Center",
                    type="Cold Storage" if random.random() > 0.5 else "Dry Godown",
                    capacity_mt=random.uniform(100, 5000),
                    available_capacity_mt=random.uniform(0, 1000),
                    price_per_mt_per_day=random.uniform(1.0, 5.0),
                    rating=random.uniform(3.5, 5.0),
                    contact_number=fake.phone_number()
                )
                warehouses.append(w)
                session.add(w)

            # 4. Seed Transporters (50)
            print("Seeding Transporters...")
            transporters = []
            for i in range(50):
                t = DBTransporter(
                    transporter_id=f"TR_{i:03d}",
                    provider_name=f"{fake.company()} Logistics",
                    vehicle_type=random.choice(["Mini Truck", "Refrigerated Truck", "Standard Truck"]),
                    capacity_mt=random.uniform(1, 20),
                    rate_per_km=random.uniform(12, 30),
                    base_fare=random.uniform(500, 2000),
                    rating=random.uniform(3.5, 5.0),
                    contact_number=fake.phone_number(),
                    current_location=random.choice(MAHARASHTRA_DISTRICTS)
                )
                transporters.append(t)
                session.add(t)

            # 5. Seed Processors (20)
            print("Seeding Processors...")
            for i in range(20):
                p = DBProcessor(
                    processor_id=f"PR_{i:03d}",
                    company_name=f"{fake.company()} Foods",
                    crop_accepted=random.choice(CROPS),
                    capacity_mt=random.uniform(500, 10000),
                    purchase_price_per_kg=random.uniform(10, 20),
                    district=random.choice(MAHARASHTRA_DISTRICTS)
                )
                session.add(p)

            # 6. Seed Compost (15)
            print("Seeding Compost Plants...")
            for i in range(15):
                c = DBCompost(
                    plant_id=f"CP_{i:03d}",
                    plant_name=f"{fake.company()} BioWaste",
                    waste_accepted="Tomato, Onion, Grapes, Banana",
                    capacity_mt=random.uniform(1000, 5000),
                    district=random.choice(MAHARASHTRA_DISTRICTS)
                )
                session.add(c)
                
            # 7. Seed Historical Negotiations (1000)
            print("Seeding Historical Negotiations (1000 deals)...")
            history_data = []
            for i in range(1000):
                f = random.choice(farmers)
                b = random.choice(buyers)
                success = random.random() > 0.3
                final_price = random.uniform(20, 50) if success else None
                n = DBNegotiation(
                    negotiation_id=f"NEG_{i:05d}",
                    crop=b.crop,
                    quantity=random.uniform(100, 2000),
                    farmer_id=f.id,
                    buyer_id=b.id,
                    user_id=b.user_id,
                    farmer_name=f.name,
                    status="DEAL" if success else "REJECT",
                    current_round=random.randint(1, 5),
                    summary=f"Negotiation {'succeeded' if success else 'failed'} after rounds.",
                    final_price=final_price,
                    transport_plan="",
                    peer_node="",
                    logs=[],
                    market_offers=[],
                    selected_buyer={},
                    signatures={}
                )
                session.add(n)
                
                # Format for RAG memory
                doc_str = (
                    f"Deal ID: {n.negotiation_id}. Crop: {n.crop}, Qty: {n.quantity}kg. "
                    f"Farmer: {n.farmer_name}, Buyer: {b.buyer_name}. "
                    f"Status: {n.status}. "
                )
                if success:
                    doc_str += f"Final Price: ₹{final_price:.2f}/kg."
                else:
                    doc_str += f"Buyer Max Budget was ₹{b.max_price:.2f}/kg."
                
                history_data.append({"id": n.negotiation_id, "text": doc_str, "metadata": {"crop": n.crop, "status": n.status}})
                
        print("Committing PostgreSQL Data...")
        
    print("Seeding ChromaDB Collections...")
    # Ingest historical data into reflection memory
    vs_reflection = rag_service.vectorstores.get("reflection_memory")
    if vs_reflection:
        vs_reflection.add_texts(
            texts=[h["text"] for h in history_data],
            metadatas=[h["metadata"] for h in history_data],
            ids=[h["id"] for h in history_data]
        )
    
    # Also load the JSONs
    vs_crop = rag_service.vectorstores.get("crop_knowledge")
    if vs_crop:
        with open("backend/dataset/crop_knowledge.json", "r") as f:
            crop_data = json.load(f)
            docs = [json.dumps(c) for c in crop_data]
            metas = [{"crop": c["crop"]} for c in crop_data]
            ids = [f"crop_{c['crop']}" for c in crop_data]
            vs_crop.add_texts(texts=docs, metadatas=metas, ids=ids)
        
    vs_gov = rag_service.vectorstores.get("government_rules")
    if vs_gov:
        with open("backend/dataset/government_rules.json", "r") as f:
            gov_data = json.load(f)
            docs = [json.dumps(g) for g in gov_data]
            metas = [{"crop": g["crop"]} for g in gov_data]
            ids = [f"gov_{g['crop']}" for g in gov_data]
            vs_gov.add_texts(texts=docs, metadatas=metas, ids=ids)
    
    print("Database Seed and RAG Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(seed_db())
