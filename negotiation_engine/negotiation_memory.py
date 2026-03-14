class NegotiationMemory:

    def __init__(self):
        self.offers = []
        self.messages = []
        self.deal = None

    # ----------------------------------
    # Store Offer
    # ----------------------------------

    def store_offer(self, agent, offer):

        record = {
            "agent": agent,
            "offer": offer
        }

        self.offers.append(record)

    # ----------------------------------
    # Store Conversation Message
    # ----------------------------------

    def store_message(self, agent, message):

        msg = {
            "agent": agent,
            "message": message
        }

        self.messages.append(msg)

    # ----------------------------------
    # Store Final Deal
    # ----------------------------------

    def store_deal(self, deal):

        self.deal = deal

    # ----------------------------------
    # Get Deal
    # ----------------------------------

    def get_deal(self):

        return self.deal

    # ----------------------------------
    # Get Offer History
    # ----------------------------------

    def get_offers(self):

        return self.offers

    # ----------------------------------
    # Get Message History
    # ----------------------------------

    def get_messages(self):

        return self.messages

    # ----------------------------------
    # Print Full Conversation
    # ----------------------------------

    def print_conversation(self):

        print("\n--- Negotiation Conversation ---\n")

        for msg in self.messages:
            print(f"{msg['agent']}: {msg['message']}")

        if self.deal:
            print("\nFinal Deal:")
            print(self.deal)