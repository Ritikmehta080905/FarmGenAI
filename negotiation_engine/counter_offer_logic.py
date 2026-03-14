class CounterOfferLogic:

    def __init__(self, max_price_jump=5):
        """
        max_price_jump controls how much price can change
        in a single negotiation step.
        """
        self.max_price_jump = max_price_jump

    # -------------------------------------
    # Process Counter Offer
    # -------------------------------------

    def process_counter_offer(self, response):

        """
        Standardizes counter-offer structure
        and ensures negotiation stability.
        """

        offer = {
            "type": response.get("type", "COUNTER"),
            "price": response.get("price"),
            "quantity": response.get("quantity"),
            "message": response.get("message")
        }

        return offer

    # -------------------------------------
    # Limit Price Jump
    # -------------------------------------

    def limit_price_jump(self, previous_price, new_price):

        """
        Prevent unrealistic jumps in price.
        """

        difference = new_price - previous_price

        if abs(difference) > self.max_price_jump:

            if difference > 0:
                new_price = previous_price + self.max_price_jump
            else:
                new_price = previous_price - self.max_price_jump

        return new_price

    # -------------------------------------
    # Validate Quantity
    # -------------------------------------

    def validate_quantity(self, quantity):

        """
        Ensures quantity is valid.
        """

        if quantity is None:
            return False

        if quantity <= 0:
            return False

        return True

    # -------------------------------------
    # Normalize Counter Offer
    # -------------------------------------

    def normalize_counter_offer(self, previous_offer, counter_offer):

        """
        Adjusts counter offer based on negotiation constraints.
        """

        previous_price = previous_offer.get("price")
        new_price = counter_offer.get("price")

        if previous_price is not None and new_price is not None:

            adjusted_price = self.limit_price_jump(previous_price, new_price)

            counter_offer["price"] = adjusted_price

        return counter_offer