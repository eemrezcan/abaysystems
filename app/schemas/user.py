# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List

class UserOut(BaseModel):
    id: UUID
    username: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

# ---- Dealer (Bayi) şemaları ----
class DealerInviteCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None
    owner_name: Optional[str] = None
    city: Optional[str] = None

class DealerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    owner_name: Optional[str] = None
    city: Optional[str] = None
    status: Optional[Literal["active", "invited", "suspended"]] = None

class DealerOut(BaseModel):
    id: UUID
    username: Optional[str]
    role: Literal["dealer", "admin"] = "dealer"
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    owner_name: Optional[str]
    city: Optional[str]
    status: Literal["invited", "active", "suspended"]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # (Pydantic v1) — v2 kullanıyorsan: from_attributes = True

class DealerPageOut(BaseModel):
    items: List[DealerOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
# ---- Auth akış şemaları ----
class AcceptInviteIn(BaseModel):
    token: str = Field(..., min_length=32)                 # maildeki token
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str = Field(..., min_length=32)
    password: str = Field(..., min_length=8)

class ChangePasswordIn(BaseModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
