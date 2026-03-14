def calculate_counter_offer(min_price: float, buyer_offer: float) -> float:
    if buyer_offer >= min_price:
        return buyer_offer
    return round((buyer_offer + min_price) / 2, 2)