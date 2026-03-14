from uuid import uuid4
from copy import deepcopy


class Database:
    users = {}
    farmers = {}
    produce = {}
    negotiations = {}
    offers = {}
    contracts = {}
    history = {}

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:8]}"

    @classmethod
    def reset(cls):
        cls.users = {}
        cls.farmers = {}
        cls.produce = {}
        cls.negotiations = {}
        cls.offers = {}
        cls.contracts = {}
        cls.history = {}

    @classmethod
    def upsert_farmer(cls, farmer_payload: dict) -> dict:
        farmer_id = farmer_payload.get("id") or cls.generate_id("farmer")
        payload = deepcopy(farmer_payload)
        payload["id"] = farmer_id
        cls.farmers[farmer_id] = payload
        return payload

    @classmethod
    def create_produce(cls, produce_payload: dict) -> dict:
        produce_id = cls.generate_id("produce")
        payload = deepcopy(produce_payload)
        payload["id"] = produce_id
        cls.produce[produce_id] = payload
        return payload

    @classmethod
    def create_negotiation(cls, negotiation_payload: dict) -> dict:
        negotiation_id = negotiation_payload.get("negotiation_id") or cls.generate_id("neg")
        payload = deepcopy(negotiation_payload)
        payload["negotiation_id"] = negotiation_id
        cls.negotiations[negotiation_id] = payload
        return payload

    @classmethod
    def append_offer(cls, negotiation_id: str, offer_payload: dict) -> dict:
        offer_id = cls.generate_id("offer")
        payload = deepcopy(offer_payload)
        payload["id"] = offer_id
        payload["negotiation_id"] = negotiation_id
        cls.offers[offer_id] = payload
        return payload

    @classmethod
    def get_offers_for_negotiation(cls, negotiation_id: str) -> list:
        offers = [offer for offer in cls.offers.values() if offer["negotiation_id"] == negotiation_id]
        return sorted(offers, key=lambda item: item.get("round", 0))

    @classmethod
    def create_contract(cls, contract_payload: dict) -> dict:
        contract_id = cls.generate_id("contract")
        payload = deepcopy(contract_payload)
        payload["id"] = contract_id
        cls.contracts[contract_id] = payload
        return payload