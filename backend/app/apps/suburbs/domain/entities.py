from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Suburb:
    name: str
    latitude: Decimal
    longitude: Decimal
