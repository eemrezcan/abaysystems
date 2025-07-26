from pydantic import BaseModel, Field
from typing import Annotated, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


NameStr = Annotated[str, Field(min_length=1, max_length=50)]
TypeStr = Annotated[str, Field(pattern="^(profile|glass)$")]


class ColorBase(BaseModel):
    name: NameStr
    type: TypeStr
    unit_cost: Decimal  # TL/kg veya TL/m²

class ColorCreate(ColorBase):
    pass

class ColorUpdate(BaseModel):
    name: Optional[NameStr] = None
    unit_cost: Optional[Decimal] = None

class ColorOut(ColorBase):
    id: UUID

    class Config:
        orm_mode = True
