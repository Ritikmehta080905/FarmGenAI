class NegotiationManager:

    def __init__(self, farmer, buyer, max_rounds=10):

        self.farmer = farmer
        self.buyer = buyer
        self.max_rounds = max_rounds

        self.log = []

    # ----------------------------------------
    # Start negotiation
    # ----------------------------------------

    def start_negotiation(self):

        round_count = 0

        # Farmer makes the first offer
        farmer_offer = self.farmer.make_offer()

        self.log.append(farmer_offer["message"])

        current_offer = {
            "price": farmer_offer["price"],
            "quantity": farmer_offer["quantity"]
        }

        # Negotiation loop
        while round_count < self.max_rounds:

            round_count += 1

            # --------------------------------
            # Buyer evaluates farmer offer
            # --------------------------------

            buyer_response = self.buyer.respond_to_offer(current_offer)

            self.log.append(buyer_response["message"])

            response_type = buyer_response["type"]

            # Buyer accepts deal
            if response_type == "ACCEPT":

                self.log.append(
                    f"Deal finalized at ₹{buyer_response['price']}/kg "
                    f"for {buyer_response['quantity']}kg"
                )

                return True

            # Buyer rejects completely
            if response_type == "REJECT":

                self.log.append("Buyer rejected the deal.")

                return False

            # Buyer counter-offer
            if response_type == "COUNTER":

                current_offer = {
                    "price": buyer_response["price"],
                    "quantity": buyer_response["quantity"]
                }

            # --------------------------------
            # Farmer evaluates buyer counter
            # --------------------------------

            farmer_response = self.farmer.respond_to_offer(current_offer)

            self.log.append(farmer_response["message"])

            response_type = farmer_response["type"]

            # Farmer accepts deal
            if response_type == "ACCEPT":

                self.log.append(
                    f"Deal finalized at ₹{farmer_response['price']}/kg "
                    f"for {farmer_response['quantity']}kg"
                )

                return True

            # Farmer rejects deal
            if response_type == "REJECT":

                self.log.append("Farmer rejected the deal.")

                return False

            # Farmer counter-offer
            if response_type == "COUNTER":

                current_offer = {
                    "price": farmer_response["price"],
                    "quantity": farmer_response["quantity"]
                }

        # --------------------------------
        # Negotiation failed
        # --------------------------------

        self.log.append("Negotiation failed: maximum rounds reached.")

        return False