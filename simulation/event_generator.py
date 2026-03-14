import random
import time


class EventGenerator:
    """
    EventGenerator creates simulation events that trigger
    negotiations and supply chain activities.

    Events generated:
    - NEW_PRODUCE
    - BUYER_REQUEST
    - STORAGE_REQUEST
    - TRANSPORT_REQUEST
    - SPOILAGE_WARNING
    """

    def __init__(self):

        self.events = []

    # -------------------------------------------------
    # Farmer harvest event
    # -------------------------------------------------

    def generate_harvest_event(self, farmer):

        quantity = random.randint(200, 1500)

        event = {
            "type": "NEW_PRODUCE",
            "farmer": farmer,
            "crop": farmer.crop_type,
            "quantity": quantity,
            "message": f"{farmer.name} harvested {quantity}kg of {farmer.crop_type}"
        }

        self.events.append(event)

        return event

    # -------------------------------------------------
    # Buyer demand event
    # -------------------------------------------------

    def generate_buyer_request(self, buyer, crop):

        quantity = random.randint(100, 1000)

        event = {
            "type": "BUYER_REQUEST",
            "buyer": buyer,
            "crop": crop,
            "quantity": quantity,
            "message": f"{buyer.name} requests {quantity}kg of {crop}"
        }

        self.events.append(event)

        return event

    # -------------------------------------------------
    # Storage request event
    # -------------------------------------------------

    def generate_storage_request(self, farmer, quantity):

        event = {
            "type": "STORAGE_REQUEST",
            "farmer": farmer,
            "quantity": quantity,
            "message": f"{farmer.name} requests storage for {quantity}kg"
        }

        self.events.append(event)

        return event

    # -------------------------------------------------
    # Transport request event
    # -------------------------------------------------

    def generate_transport_request(self, quantity, distance):

        event = {
            "type": "TRANSPORT_REQUEST",
            "quantity": quantity,
            "distance": distance,
            "message": f"Transport required for {quantity}kg over {distance}km"
        }

        self.events.append(event)

        return event

    # -------------------------------------------------
    # Spoilage warning event
    # -------------------------------------------------

    def generate_spoilage_warning(self, farmer):

        event = {
            "type": "SPOILAGE_WARNING",
            "farmer": farmer,
            "message": f"Warning: {farmer.name}'s produce may spoil soon"
        }

        self.events.append(event)

        return event

    # -------------------------------------------------
    # Random event generator
    # -------------------------------------------------

    def generate_random_event(self, farmer=None, buyer=None):

        event_types = [
            "NEW_PRODUCE",
            "BUYER_REQUEST",
            "STORAGE_REQUEST",
            "TRANSPORT_REQUEST",
            "SPOILAGE_WARNING"
        ]

        event_type = random.choice(event_types)

        if event_type == "NEW_PRODUCE" and farmer:

            return self.generate_harvest_event(farmer)

        elif event_type == "BUYER_REQUEST" and buyer:

            crop = getattr(buyer, "crop_type", "unknown")
            return self.generate_buyer_request(buyer, crop)

        elif event_type == "STORAGE_REQUEST" and farmer:

            quantity = random.randint(100, 800)
            return self.generate_storage_request(farmer, quantity)

        elif event_type == "TRANSPORT_REQUEST":

            quantity = random.randint(100, 800)
            distance = random.randint(10, 200)

            return self.generate_transport_request(quantity, distance)

        elif event_type == "SPOILAGE_WARNING" and farmer:

            return self.generate_spoilage_warning(farmer)

        return None

    # -------------------------------------------------
    # Get event history
    # -------------------------------------------------

    def get_event_log(self):

        return self.events

    # -------------------------------------------------
    # Clear events
    # -------------------------------------------------

    def clear_events(self):

        self.events = []

    # -------------------------------------------------
    # Debug run
    # -------------------------------------------------

if __name__ == "__main__":

    print("\n--- Event Generator Test ---\n")

    class DummyFarmer:
        def __init__(self):
            self.name = "Farmer_Ramesh"
            self.crop_type = "wheat"

    class DummyBuyer:
        def __init__(self):
            self.name = "Buyer_1"
            self.crop_type = "wheat"

    farmer = DummyFarmer()
    buyer = DummyBuyer()

    generator = EventGenerator()

    for i in range(5):

        event = generator.generate_random_event(farmer, buyer)

        if event:
            print(event["message"])

        time.sleep(1)

    print("\nEvent Log:\n")

    for e in generator.get_event_log():
        print(e["type"], "-", e["message"])