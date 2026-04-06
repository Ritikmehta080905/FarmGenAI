import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
import json

def seed_more_data():
    # Seed more farmers
    farmers = [
        {"id": "farmer_maharashtra_1", "name": "Rajesh Kumar", "location": "Nashik, Maharashtra", "language": "Marathi"},
        {"id": "farmer_maharashtra_2", "name": "Sita Devi", "location": "Pune, Maharashtra", "language": "Marathi"},
        {"id": "farmer_karnataka_1", "name": "Anand Rao", "location": "Bangalore, Karnataka", "language": "Kannada"},
        {"id": "farmer_karnataka_2", "name": "Lakshmi Bai", "location": "Mysore, Karnataka", "language": "Kannada"},
        {"id": "farmer_gujarat_1", "name": "Vijay Patel", "location": "Ahmedabad, Gujarat", "language": "Gujarati"},
        {"id": "farmer_gujarat_2", "name": "Meera Shah", "location": "Surat, Gujarat", "language": "Gujarati"},
        {"id": "farmer_punjab_1", "name": "Gurpreet Singh", "location": "Ludhiana, Punjab", "language": "Punjabi"},
        {"id": "farmer_punjab_2", "name": "Harpreet Kaur", "location": "Amritsar, Punjab", "language": "Punjabi"},
        {"id": "farmer_up_1", "name": "Ramu Yadav", "location": "Lucknow, UP", "language": "Hindi"},
        {"id": "farmer_up_2", "name": "Sunita Sharma", "location": "Kanpur, UP", "language": "Hindi"},
    ]

    # Seed more buyers with diverse strategies
    buyers = [
        {"id": "buyer_local_mandi_2", "data": json.dumps({"name": "Kalyan Mandi", "location": "Kalyan", "strategy": "Market Option", "max_quantity": 500, "target_price": 18, "budget": 12000})},
        {"id": "buyer_local_mandi_3", "data": json.dumps({"name": "Thane Mandi", "location": "Thane", "strategy": "Market Option", "max_quantity": 600, "target_price": 17, "budget": 13000})},
        {"id": "buyer_interstate_1", "data": json.dumps({"name": "Delhi Wholesale", "location": "Delhi", "strategy": "Market Option", "max_quantity": 2000, "target_price": 16, "budget": 40000})},
        {"id": "buyer_interstate_2", "data": json.dumps({"name": "Mumbai Retail Chain", "location": "Mumbai", "strategy": "Best Profit", "max_quantity": 800, "target_price": 35, "budget": 30000})},
        {"id": "buyer_export_1", "data": json.dumps({"name": "Global Exports Ltd", "location": "Mumbai", "strategy": "Best Profit", "max_quantity": 5000, "target_price": 30, "budget": 150000})},
        {"id": "buyer_restaurant_1", "data": json.dumps({"name": "Spice Route Restaurant", "location": "Pune", "strategy": "Best Profit", "max_quantity": 200, "target_price": 40, "budget": 10000})},
        {"id": "buyer_restaurant_2", "data": json.dumps({"name": "Farm Fresh Cafe", "location": "Bangalore", "strategy": "Best Profit", "max_quantity": 150, "target_price": 45, "budget": 8000})},
        {"id": "buyer_hotel_1", "data": json.dumps({"name": "Heritage Hotel", "location": "Jaipur", "strategy": "Market Option", "max_quantity": 300, "target_price": 25, "budget": 8000})},
        {"id": "buyer_supermarket_1", "data": json.dumps({"name": "BigBasket Outlet", "location": "Chennai", "strategy": "Market Option", "max_quantity": 1000, "target_price": 22, "budget": 25000})},
        {"id": "buyer_processor_1", "data": json.dumps({"name": "Taste Buds Processing", "location": "Hyderabad", "strategy": "Market Option", "max_quantity": 3000, "target_price": 15, "budget": 50000})},
    ]

    # Seed produce listings
    produce = [
        {"id": "produce_tomato_mah_1", "farmer_name": "Rajesh Kumar", "crop": "Tomato", "quantity": 500, "min_price": 20, "shelf_life": 5, "quality": "A", "location": "Nashik", "language": "Marathi", "status": "active"},
        {"id": "produce_onion_mah_1", "farmer_name": "Sita Devi", "crop": "Onion", "quantity": 800, "min_price": 15, "shelf_life": 30, "quality": "B", "location": "Pune", "language": "Marathi", "status": "active"},
        {"id": "produce_potato_kar_1", "farmer_name": "Anand Rao", "crop": "Potato", "quantity": 1000, "min_price": 18, "shelf_life": 60, "quality": "A", "location": "Bangalore", "language": "Kannada", "status": "active"},
        {"id": "produce_leafy_kar_1", "farmer_name": "Lakshmi Bai", "crop": "Spinach", "quantity": 200, "min_price": 25, "shelf_life": 3, "quality": "A", "location": "Mysore", "language": "Kannada", "status": "active"},
        {"id": "produce_cotton_guj_1", "farmer_name": "Vijay Patel", "crop": "Cotton", "quantity": 1500, "min_price": 50, "shelf_life": 365, "quality": "B", "location": "Ahmedabad", "language": "Gujarati", "status": "active"},
        {"id": "produce_rice_guj_1", "farmer_name": "Meera Shah", "crop": "Rice", "quantity": 2000, "min_price": 30, "shelf_life": 180, "language": "Gujarati", "status": "active"},
        {"id": "produce_wheat_pun_1", "farmer_name": "Gurpreet Singh", "crop": "Wheat", "quantity": 3000, "min_price": 25, "shelf_life": 120, "quality": "A", "location": "Ludhiana", "language": "Punjabi", "status": "active"},
        {"id": "produce_maize_pun_1", "farmer_name": "Harpreet Kaur", "crop": "Maize", "quantity": 1200, "min_price": 20, "shelf_life": 90, "quality": "B", "location": "Amritsar", "language": "Punjabi", "status": "active"},
        {"id": "produce_sugarcane_up_1", "farmer_name": "Ramu Yadav", "crop": "Sugarcane", "quantity": 5000, "min_price": 5, "shelf_life": 7, "quality": "A", "location": "Lucknow", "language": "Hindi", "status": "active"},
        {"id": "produce_mustard_up_1", "farmer_name": "Sunita Sharma", "crop": "Mustard", "quantity": 400, "min_price": 60, "shelf_life": 180, "quality": "A", "location": "Kanpur", "language": "Hindi", "status": "active"},
    ]

    conn = sqlite3.connect('agrinegotiator.db')
    c = conn.cursor()

    # Insert farmers
    for f in farmers:
        c.execute("INSERT OR IGNORE INTO farmers (id, name, location, language) VALUES (?, ?, ?, ?)",
                  (f["id"], f["name"], f["location"], f["language"]))

    # Insert buyers
    for b in buyers:
        c.execute("INSERT OR IGNORE INTO buyers (id, data) VALUES (?, ?)", (b["id"], b["data"]))

    # Insert produce
    for p in produce:
        c.execute("INSERT OR IGNORE INTO produce (id, data) VALUES (?, ?)", (p["id"], json.dumps(p)))

    conn.commit()
    conn.close()
    print("Seeded additional data: 10 farmers, 10 buyers, 10 produce listings.")

if __name__ == "__main__":
    seed_more_data()