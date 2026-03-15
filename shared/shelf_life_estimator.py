"""Shelf-life utilities for decision-making in escalation logic."""


CROP_DEFAULT_SHELF_LIFE = {
    "Tomato":    4,
    "Onion":     14,
    "Spinach":   2,
    "Capsicum":  5,
    "Cabbage":   6,
    "Wheat":     180,
    "Rice":      180,
    "Sugarcane": 7,
    "Maize":     30,
}


def default_shelf_life(crop: str) -> int:
    """Return default shelf life in days for a given crop name."""
    return CROP_DEFAULT_SHELF_LIFE.get(crop, 4)


def is_critical(shelf_life_days: int, threshold: int = 2) -> bool:
    """Return True if shelf life is at or below the critical threshold."""
    return shelf_life_days <= threshold


def urgency_level(shelf_life_days: int) -> str:
    """Return 'critical' | 'urgent' | 'normal'."""
    if shelf_life_days <= 2:
        return "critical"
    if shelf_life_days <= 4:
        return "urgent"
    return "normal"
