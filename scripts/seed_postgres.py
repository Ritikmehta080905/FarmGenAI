import sys
import os
import json
import csv
import asyncio
from sqlalchemy import select, delete

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import (
    AsyncSessionLocal,
    DBMspPrice,
    DBMarketMapping,
    DBCropQualityReference,
    DBWarehouse,
    DBTransporter,
    DBTrustScore,
    DBSeasonalCalendar,
    engine
)

async def seed_data():
    print("Database seeding initiated...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Seed MSP Prices
            msp_file = r"c:\PROJECT\FarmGenAI\backend\dataset\cleaned_msp_prices.json"
            if os.path.exists(msp_file):
                with open(msp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Clean existing to prevent duplicates on re-run
                await session.execute(delete(DBMspPrice))
                
                for item in data:
                    db_item = DBMspPrice(
                        crop=item["crop"],
                        crop_full_name=item.get("crop_full_name"),
                        group=item.get("group"),
                        year=item["year"],
                        msp_price_per_quintal=item["msp_price_per_quintal"]
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} MSP price records.")

            # 2. Seed Market Mapping
            mapping_file = r"c:\PROJECT\FarmGenAI\backend\dataset\maharashtra_market_mapping.csv"
            if os.path.exists(mapping_file):
                await session.execute(delete(DBMarketMapping))
                with open(mapping_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    count = 0
                    for row in reader:
                        db_item = DBMarketMapping(
                            district=row["district"],
                            market_name=row["market_name"],
                            state=row["state"]
                        )
                        session.add(db_item)
                        count += 1
                print(f"Seeded {count} market mapping records.")

            # 3. Seed Crop Quality References
            quality_file = r"c:\PROJECT\FarmGenAI\backend\dataset\crop_quality_references.json"
            if os.path.exists(quality_file):
                await session.execute(delete(DBCropQualityReference))
                with open(quality_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    db_item = DBCropQualityReference(
                        crop=item["crop"],
                        variety=item["variety"],
                        grade=item["grade"],
                        min_size_mm=item.get("min_size_mm"),
                        max_moisture_pct=item.get("max_moisture_pct"),
                        color_standards=item.get("color_standards"),
                        skin_firmness=item.get("skin_firmness"),
                        common_defects_allowed=item.get("common_defects_allowed")
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} crop quality reference records.")

            # 4. Seed Warehouses
            warehouse_file = r"c:\PROJECT\FarmGenAI\backend\dataset\warehouses.json"
            if os.path.exists(warehouse_file):
                await session.execute(delete(DBWarehouse))
                with open(warehouse_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    db_item = DBWarehouse(
                        warehouse_id=item["warehouse_id"],
                        name=item["name"],
                        district=item["district"],
                        location=item["location"],
                        type=item["type"],
                        capacity_mt=item["capacity_mt"],
                        available_capacity_mt=item["available_capacity_mt"],
                        price_per_mt_per_day=item["price_per_mt_per_day"],
                        rating=item.get("rating"),
                        contact_number=item.get("contact_number")
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} warehouse records.")

            # 5. Seed Transporters
            transport_file = r"c:\PROJECT\FarmGenAI\backend\dataset\transporters.json"
            if os.path.exists(transport_file):
                await session.execute(delete(DBTransporter))
                with open(transport_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    db_item = DBTransporter(
                        transporter_id=item["transporter_id"],
                        provider_name=item["provider_name"],
                        vehicle_type=item["vehicle_type"],
                        capacity_mt=item["capacity_mt"],
                        rate_per_km=item["rate_per_km"],
                        base_fare=item["base_fare"],
                        rating=item.get("rating"),
                        contact_number=item.get("contact_number"),
                        current_location=item.get("current_location")
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} transporter records.")

            # 6. Seed Trust Scores
            trust_file = r"c:\PROJECT\FarmGenAI\backend\dataset\trust_scores.json"
            if os.path.exists(trust_file):
                await session.execute(delete(DBTrustScore))
                with open(trust_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    db_item = DBTrustScore(
                        user_id=item["user_id"],
                        name=item["name"],
                        role=item["role"],
                        average_rating=item.get("average_rating", 4.0),
                        fulfillment_rate=item.get("fulfillment_rate", 100.0),
                        payment_punctuality=item.get("payment_punctuality", 100.0),
                        total_completed_deals=item.get("total_completed_deals", 0),
                        contract_breaches=item.get("contract_breaches", 0),
                        trust_score_final=item.get("trust_score_final", 4.0)
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} trust score records.")

            # 7. Seed Seasonal Calendar
            calendar_file = r"c:\PROJECT\FarmGenAI\backend\dataset\seasonal_calendar.json"
            if os.path.exists(calendar_file):
                await session.execute(delete(DBSeasonalCalendar))
                with open(calendar_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    db_item = DBSeasonalCalendar(
                        season_id=item["season_id"],
                        event_name=item["event_name"],
                        month_range=item["month_range"],
                        affected_crops=",".join(item["affected_crops"]),
                        price_impact_trend=item["price_impact_trend"],
                        market_behavior_description=item.get("market_behavior_description")
                    )
                    session.add(db_item)
                print(f"Seeded {len(data)} seasonal calendar records.")

    await engine.dispose()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
