from uuid import uuid4


class Database:
    users = {}
    farmers = {}
    produce = {}
    negotiations = {}
    offers = {}
    history = {}

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:8]}"