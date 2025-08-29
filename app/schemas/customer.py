# app/schemas/customer.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class CustomerBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=100)
    name: str         = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    city: Optional[str]  = Field(None, max_length=100)

class CustomerCreate(CustomerBase):
    """Yeni müşteri oluşturma payload’ı"""
    pass

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str]         = Field(None, min_length=1, max_length=100)
    phone: Optional[str]        = Field(None, max_length=20)
    city: Optional[str]         = Field(None, max_length=100)

    class Config:
        orm_mode = True

class CustomerOut(CustomerBase):
    id: UUID
    dealer_id: UUID
    is_deleted: bool
    created_at: datetime

    class Config:
        orm_mode = True

class CustomerPageOut(BaseModel):
    items: List[CustomerOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool