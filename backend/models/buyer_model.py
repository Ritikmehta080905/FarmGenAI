from pydantic import BaseModel


class BuyerResponse(BaseModel):
    name: str
    crop: str