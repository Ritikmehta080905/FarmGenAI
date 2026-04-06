import requests
import json

try:
    resp = requests.post(
        'http://localhost:8000/run-simulation',
        json={
            'scenario': 'direct-sale',
            'user_id': 'audit_user',
            'farmer_name': 'Audit Farmer',
            'crop': 'Tomato',
            'quantity': 45,
            'min_price': 18,
            'shelf_life': 5,
            'location': 'Mumbai',
            'quality': 'A'
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        print("Selected Buyer:")
        print(json.dumps(data.get('selected_buyer', {}), indent=2))
        
        print("\nAll Market Offers:")
        for off in data.get('market_offers', []):
            print(f"- {off['buyer_name']} ({off['strategy']}): ₹{off['offered_price']} (Score: {off['score']})")
    else:
        print("API Error:", resp.status_code, resp.text)
except Exception as e:
    print("Exception:", str(e))
