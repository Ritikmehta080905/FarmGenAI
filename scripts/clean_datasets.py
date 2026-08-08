import csv
import json
import os
import re

raw_csv_path = r"c:\Users\gayat\Downloads\FarmGenAI\backend\dataset\Market_Wise_Price_Arrival_06-08-2026_08-18-20_PM.csv"
cleaned_mandi_path = r"c:\Users\gayat\Downloads\FarmGenAI\backend\dataset\cleaned_mandi_prices.json"
cleaned_msp_path = r"c:\Users\gayat\Downloads\FarmGenAI\backend\dataset\cleaned_msp_prices.json"

def clean_data():
    if not os.path.exists(raw_csv_path):
        print(f"Error: Raw CSV file not found at {raw_csv_path}")
        return

    mandi_records = []
    msp_records = []

    with open(raw_csv_path, mode='r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        
        # Row 0 and 1 are titles. Row 2 is the actual header.
        header = [h.strip() for h in reader[2]]
        data_rows = reader[3:]

        # Extract dates from headers like "Price on 04 Aug, 2026"
        price_cols = {}  # col_idx: date_str
        arrival_cols = {} # col_idx: date_str
        
        for idx, name in enumerate(header):
            if "Price on" in name:
                date_match = re.search(r"Price on (.+)", name)
                if date_match:
                    price_cols[idx] = date_match.group(1).strip()
            elif "Arrival on" in name:
                date_match = re.search(r"Arrival on (.+)", name)
                if date_match:
                    arrival_cols[idx] = date_match.group(1).strip()

        print(f"Detected Price columns for dates: {list(price_cols.values())}")
        print(f"Detected Arrival columns for dates: {list(arrival_cols.values())}")

        for row in data_rows:
            if not row or len(row) < len(header):
                continue
            
            group = row[0].strip()
            commodity = row[1].strip()
            msp_val = row[2].strip()

            # Clean commodity name (e.g., "Bajra(Pearl Millet/Cumbu)" -> "Bajra")
            clean_commodity = re.sub(r"\(.*\)", "", commodity).strip()

            # 1. Parse MSP
            try:
                msp_float = float(msp_val)
                msp_records.append({
                    "crop": clean_commodity,
                    "crop_full_name": commodity,
                    "group": group,
                    "year": "2026-27",
                    "msp_price_per_quintal": msp_float
                })
            except ValueError:
                pass

            # 2. Parse daily prices and arrivals
            # Iterate through each price date
            for p_idx, p_date in price_cols.items():
                price_str = row[p_idx].strip()
                if not price_str or price_str == "-":
                    continue

                # Find corresponding arrival column index for the same date
                a_idx = None
                for idx, a_date in arrival_cols.items():
                    if a_date == p_date:
                        a_idx = idx
                        break
                
                arrival_str = row[a_idx].strip() if a_idx is not None else "-"
                if arrival_str == "-":
                    arrival_str = "0.0"

                try:
                    price_float = float(price_str)
                    arrival_float = float(arrival_str)
                    
                    mandi_records.append({
                        "crop": clean_commodity,
                        "crop_full_name": commodity,
                        "group": group,
                        "date": p_date,
                        "price_per_quintal": price_float,
                        "arrival_mt": arrival_float,
                        "state": "Maharashtra",
                        # We use representative major mandis for districts since this is state-level data
                        "mandi_name": "Maharashtra APMC average"
                    })
                except ValueError as e:
                    print(f"Skipping row for {commodity} on {p_date} due to parsing error: {e}")

    # Write output JSONs
    with open(cleaned_mandi_path, 'w', encoding='utf-8') as f:
        json.dump(mandi_records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(mandi_records)} cleaned daily mandi records to {cleaned_mandi_path}")

    with open(cleaned_msp_path, 'w', encoding='utf-8') as f:
        json.dump(msp_records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(msp_records)} cleaned MSP records to {cleaned_msp_path}")

if __name__ == "__main__":
    clean_data()
