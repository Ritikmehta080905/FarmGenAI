"""Minimal price utility helpers used across agents and scenarios."""


def midpoint_price(price_a: float, price_b: float) -> float:
    """Return the midpoint between two prices, rounded to 2dp."""
    return round((price_a + price_b) / 2, 2)


def apply_discount(price: float, discount_pct: float) -> float:
    """Return price reduced by discount_pct percent."""
    return round(price * (1 - discount_pct / 100), 2)


def storage_cost_total(quantity_kg: float, cost_per_kg: float) -> float:
    """Total storage cost for given quantity."""
    return round(quantity_kg * cost_per_kg, 2)


def effective_sale_price(price: float, transport_cost_per_kg: float) -> float:
    """Net price after subtracting per-kg transport cost."""
    return round(price - transport_cost_per_kg, 2)


def estimate_revenue(price: float, quantity_kg: float) -> float:
    """Gross revenue estimate."""
    return round(price * quantity_kg, 2)
