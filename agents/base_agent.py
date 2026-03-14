import uuid
from datetime import datetime


class BaseAgent:
    """
    Base class for all agents in the AgriNegotiator system.

    Provides shared capabilities:
    - Agent identity
    - Memory / logging
    - Negotiation participation
    - Standard negotiation responses
    """

    def __init__(self, name: str, agent_type: str, strategy: str = "default"):

        # Unique ID
        self.agent_id = str(uuid.uuid4())

        # Identity
        self.name = name
        self.agent_type = agent_type

        # Strategy (future: aggressive, conservative, etc.)
        self.strategy = strategy

        # Action history
        self.memory = []

        # Negotiations currently active
        self.active_negotiations = []

        # Agent state
        self.is_active = True

    # ------------------------------------------------
    # Logging System
    # ------------------------------------------------

    def log_action(self, message: str):

        timestamp = datetime.now().strftime("%H:%M:%S")

        log_entry = {
            "time": timestamp,
            "agent": self.name,
            "type": self.agent_type,
            "message": message
        }

        self.memory.append(log_entry)

        return f"{self.name}: {message}"

    def get_memory(self):
        return self.memory

    def clear_memory(self):
        self.memory = []

    # ------------------------------------------------
    # Negotiation Participation
    # ------------------------------------------------

    def join_negotiation(self, negotiation_id):

        if negotiation_id not in self.active_negotiations:
            self.active_negotiations.append(negotiation_id)

    def leave_negotiation(self, negotiation_id):

        if negotiation_id in self.active_negotiations:
            self.active_negotiations.remove(negotiation_id)

    # ------------------------------------------------
    # Standard Negotiation Responses
    # ------------------------------------------------

    def accept_offer(self, price):

        message = self.log_action(f"Accepting offer ₹{price}/kg")

        return {
            "type": "ACCEPT",
            "price": price,
            "message": message
        }

    def reject_offer(self, price):

        message = self.log_action(f"Rejecting offer ₹{price}/kg")

        return {
            "type": "REJECT",
            "price": price,
            "message": message
        }

    def counter_offer(self, price):

        message = self.log_action(f"Counter offer ₹{price}/kg")

        return {
            "type": "COUNTER",
            "price": price,
            "message": message
        }

    # ------------------------------------------------
    # Methods that child agents MUST implement
    # ------------------------------------------------

    def make_offer(self, context=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement make_offer()"
        )

    def evaluate_offer(self, offer, context=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement evaluate_offer()"
        )

    def respond_to_offer(self, offer, context=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement respond_to_offer()"
        )

    # ------------------------------------------------
    # Agent Status
    # ------------------------------------------------

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def status(self):

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "strategy": self.strategy,
            "active": self.is_active,
            "active_negotiations": len(self.active_negotiations)
        }

    # ------------------------------------------------
    # Debug Utility
    # ------------------------------------------------

    def __repr__(self):
        return f"<Agent {self.name} ({self.agent_type})>"