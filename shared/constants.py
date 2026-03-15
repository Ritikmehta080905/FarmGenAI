# Shared constants for AgriNegotiator

# Negotiation defaults
DEFAULT_MAX_ROUNDS = 5
DEFAULT_SHELF_LIFE = 4  # days
MIN_DEAL_CONVERGENCE_GAP = 2  # ₹/kg — price gap at which a deal is forced

# Market price bounds (₹/kg)
MARKET_PRICE_MIN = 10
MARket_PRICE_MAX = 35

# Crop categories
PERISHABLE_CROPS = ["Tomato", "Onion", "Spinach", "Cabbage", "Capsicum"]
STABLE_CROPS = ["Wheat", "Rice", "Sugarcane", "Maize"]

# Escalation thresholds
WAREHOUSE_MIN_CAPACITY = 100  # kg
SHELF_LIFE_CRITICAL_DAYS = 2  # escalate to compost below this

# WebSocket
WS_HOST = "localhost"
WS_PORT = 8765

# API
API_HOST = "localhost"
API_PORT = 8000
