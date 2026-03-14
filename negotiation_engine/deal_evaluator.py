class DealEvaluator:

    def __init__(self):
        pass

    # -----------------------------------
    # Check if response means acceptance
    # -----------------------------------

    def is_accepted(self, response_type):

        """
        Determines if negotiation should end
        with a successful deal.
        """

        if response_type is None:
            return False

        return response_type.upper() == "ACCEPT"

    # -----------------------------------
    # Check if response means rejection
    # -----------------------------------

    def is_rejected(self, response_type):

        if response_type is None:
            return False

        return response_type.upper() == "REJECT"

    # -----------------------------------
    # Validate price agreement
    # -----------------------------------

    def price_valid(self, price, farmer_min_price, buyer_max_price):

        if price < farmer_min_price:
            return False

        if price > buyer_max_price:
            return False

        return True

    # -----------------------------------
    # Validate quantity agreement
    # -----------------------------------

    def quantity_valid(self, quantity, farmer_qty, buyer_capacity):

        if quantity <= 0:
            return False

        if quantity > farmer_qty:
            return False

        if quantity > buyer_capacity:
            return False

        return True

    # -----------------------------------
    # Create final contract
    # -----------------------------------

    def create_contract(self, farmer, buyer, price, quantity):

        contract = {
            "farmer": farmer.name,
            "buyer": buyer.name,
            "price_per_kg": price,
            "quantity": quantity,
            "total_value": price * quantity
        }

        return contract