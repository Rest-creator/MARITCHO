from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SuburbOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    latitude: Decimal
    longitude: Decimal
