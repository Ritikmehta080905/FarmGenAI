import csv
import json
import os
import re

def parse_float(val):
    if not val or val == '-':
        return 0.0
    try:
        return float(val.replace(',', ''))
    except ValueError:
        return 0.0

def normalize_crop_name(raw_name):
    """
    Cleans names like 'Bajra(Pearl Millet/Cumbu)' -> 'Bajra'
    """
    cleaned = re.sub(r'\(.*?\)', '', raw_name).strip()
    if cleaned.lower() == 'soyabean' or cleaned.lower() == 'soybean':
        return 'Soybean'
    return cleaned

def ingest_csv():
    csv_path = r'c:\PROJECT\FarmGenAI\backend\dataset\Market_Wise_Price_Arrival_06-08-2026_08-18-20_PM.csv'
    mandi_out = r'c:\PROJECT\FarmGenAI\backend\dataset\cleaned_mandi_prices.json'
    msp_out = r'c:\PROJECT\FarmGenAI\backend\dataset\cleaned_msp_prices.json'

    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    mandi_prices = []
    msp_prices = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        lines = list(reader)

        # Skip headers (first 3 rows)
        data_rows = lines[3:]

        for row in data_rows:
            if not row or not row[0].strip():
                continue
            
            group = row[0].strip()
            raw_commodity = row[1].strip()
            commodity = normalize_crop_name(raw_commodity)
            
            msp_quintal = parse_float(row[2])
            price_04 = parse_float(row[3])
            price_03 = parse_float(row[4])
            price_02 = parse_float(row[5])
            
            arrival_04 = parse_float(row[6])
            
            # Divide by 100 to convert Rs/Quintal to Rs/kg
            msp_kg = msp_quintal / 100.0 if msp_quintal else 0.0
            price_04_kg = price_04 / 100.0 if price_04 else 0.0
            
            if msp_kg > 0:
                msp_prices.append({
                    "crop": commodity,
                    "crop_full_name": raw_commodity,
                    "msp_price_per_quintal": msp_quintal,
                    "msp_price_per_kg": msp_kg,
                    "year": "2026-27"
                })
            
            if price_04_kg > 0:
                mandi_prices.append({
                    "crop": commodity,
                    "crop_full_name": raw_commodity,
                    "date": "2026-08-04",
                    "state": "Maharashtra",
                    "mandi_name": "Regional Avg (Maharashtra)",
                    "price_per_quintal": price_04,
                    "price_per_kg": price_04_kg,
                    "arrival_mt": arrival_04
                })

    with open(mandi_out, 'w', encoding='utf-8') as f:
        json.dump(mandi_prices, f, indent=4)
        
    with open(msp_out, 'w', encoding='utf-8') as f:
        json.dump(msp_prices, f, indent=4)
        
    print(f"Successfully processed {len(mandi_prices)} market prices and {len(msp_prices)} MSP rates.")
    print("Files saved to backend/dataset/cleaned_mandi_prices.json and cleaned_msp_prices.json")

if __name__ == "__main__":
    ingest_csv()
