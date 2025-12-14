from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class CalculationHelperBase(BaseModel):
    bicak_payi: float = Field(..., description="Bıçak payı")
    boya_payi: float = Field(..., description="Boya payı")


class CalculationHelperUpdate(CalculationHelperBase):
    """Payload for creating/updating helper values"""
    pass


class CalculationHelperOut(CalculationHelperBase):
    id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    is_default: bool = Field(..., description="Değerler admin varsayılanından mı geliyor?")
    has_record: bool = Field(..., description="Veritabanında gerçek kayıt var mı?")

    class Config:
        orm_mode = True
