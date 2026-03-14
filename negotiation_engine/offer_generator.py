class OfferGenerator:

    def __init__(self):
        pass

    # --------------------------------------
    # Generate initial farmer offer
    # --------------------------------------

    def generate_farmer_offer(self, farmer):

        offer = farmer.make_offer()

        # Standardize structure
        standardized_offer = {
            "type": "OFFER",
            "price": offer["price"],
            "quantity": offer["quantity"],
            "message": offer["message"]
        }

        return standardized_offer

    # --------------------------------------
    # Generate buyer offer (optional future)
    # --------------------------------------

    def generate_buyer_offer(self, buyer, context):

        response = buyer.make_offer(context)

        standardized_offer = {
            "type": response.get("type", "OFFER"),
            "price": response.get("price"),
            "quantity": response.get("quantity"),
            "message": response.get("message")
        }

        return standardized_offer