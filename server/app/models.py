from pydantic import BaseModel
from datetime import datetime


class UserRate(BaseModel):
    user_email: str
    origin: str
    destination: str
    effective_date: str
    expiry_date: str
    price: float
    annual_volume: float
