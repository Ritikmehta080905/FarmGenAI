from pydantic import BaseModel


class FarmerResponse(BaseModel):
    id: str
    name: str
    location: str
    language: str