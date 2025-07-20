# app/schemas/order.py
from uuid import UUID
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

# --- Input Schemas ---
class OrderItemProfileIn(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    total_weight_kg: Optional[float] = None

class OrderItemGlassIn(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    area_m2: Optional[float] = None

class OrderItemMaterialIn(BaseModel):
    material_id: UUID
    cut_length_mm: Optional[float] = None
    count: int

class OrderItemExtraMaterialIn(BaseModel):
    material_id: UUID
    cut_length_mm: Optional[float] = None
    count: int

class OrderItemIn(BaseModel):
    project_system_id: UUID
    color: Optional[str] = None
    width_mm: float
    height_mm: float
    quantity: int
    profiles: List[OrderItemProfileIn] = []
    glasses: List[OrderItemGlassIn] = []
    materials: List[OrderItemMaterialIn] = []
    extra_materials: List[OrderItemExtraMaterialIn] = []

class SalesOrderCreate(BaseModel):
    order_no: str
    order_date: date
    order_name: Optional[str] = None
    project_id: UUID
    customer_id: UUID
    status: str
    created_by: UUID
    items: List[OrderItemIn]

# --- Update Schema ---
class SalesOrderUpdate(BaseModel):
    status: Optional[str] = None

# --- Output Schemas ---
class OrderItemProfileOut(OrderItemProfileIn):
    id: UUID

    class Config:
        orm_mode = True

class OrderItemGlassOut(OrderItemGlassIn):
    id: UUID

    class Config:
        orm_mode = True

class OrderItemMaterialOut(OrderItemMaterialIn):
    id: UUID

    class Config:
        orm_mode = True

class OrderItemExtraMaterialOut(OrderItemExtraMaterialIn):
    id: UUID

    class Config:
        orm_mode = True

class OrderItemOut(OrderItemIn):
    id: UUID
    profiles: List[OrderItemProfileOut] = []
    glasses: List[OrderItemGlassOut] = []
    materials: List[OrderItemMaterialOut] = []
    extra_materials: List[OrderItemExtraMaterialOut] = []

    class Config:
        orm_mode = True

class SalesOrderOut(BaseModel):
    id: UUID
    order_no: str
    order_date: date
    order_name: Optional[str] = None
    project_id: UUID
    customer_id: UUID
    status: str
    created_by: UUID
    created_at: datetime
    items: List[OrderItemOut] = []

    class Config:
        orm_mode = True
