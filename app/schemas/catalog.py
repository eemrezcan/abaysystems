# app/schemas/catalog.py
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ------- Profile
class ProfileBase(BaseModel):
    profil_kodu: str = Field(..., min_length=1)
    profil_isim: str = Field(..., min_length=1)
    profil_kesit_fotograf: Optional[str]
    birim_agirlik: float
    boy_uzunluk: float
    unit_price: Optional[float] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    profil_kodu: Optional[str] = Field(None, min_length=1)
    profil_isim: Optional[str] = Field(None, min_length=1)
    profil_kesit_fotograf: Optional[str] = None
    birim_agirlik: Optional[float] = None
    boy_uzunluk: Optional[float] = None
    unit_price: Optional[float] = None

class ProfileOut(ProfileBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool  # ✅ eklendi

    class Config:
        orm_mode = True

class ProfilePageOut(BaseModel):
    items: List[ProfileOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ------- GlassType
class GlassTypeBase(BaseModel):
    cam_isim: str = Field(..., min_length=1)
    thickness_mm: float
    # birim_agirlik alanı kaldırıldı
    # ↓↓↓ yeni: opsiyonel belirteç alanları
    belirtec_1: Optional[int] = None
    belirtec_2: Optional[int] = None

class GlassTypeCreate(GlassTypeBase):
    pass

# İsteğe bağlı: update senaryoları için kısmi güncelleme şeması
class GlassTypeUpdate(BaseModel):
    cam_isim: Optional[str] = Field(None, min_length=1)
    thickness_mm: Optional[float] = None
    belirtec_1: Optional[int] = None
    belirtec_2: Optional[int] = None

class GlassTypeOut(GlassTypeBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    belirtec_1: Optional[int] = None
    belirtec_2: Optional[int] = None
    is_active: bool  # ✅ eklendi

    class Config:
        orm_mode = True

class GlassTypePageOut(BaseModel):
    items: List[GlassTypeOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ------- OtherMaterial
class OtherMaterialBase(BaseModel):
    diger_malzeme_isim: str = Field(..., min_length=1)
    birim: str = Field(..., min_length=1)
    birim_agirlik: float
    hesaplama_turu: Optional[str]
    unit_price: Optional[float] = None

class OtherMaterialCreate(OtherMaterialBase):
    pass

class OtherMaterialOut(OtherMaterialBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool  # ✅ eklendi

    class Config:
        orm_mode = True

class OtherMaterialPageOut(BaseModel):
    items: List[OtherMaterialOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ------- Remote (Kumanda)

class RemoteBase(BaseModel):
    kumanda_isim: str = Field(..., min_length=1)
    price: float
    kapasite: int

class RemoteCreate(RemoteBase):
    pass

class RemoteOut(RemoteBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool  # ✅ eklendi

    class Config:
        orm_mode = True

class RemotePageOut(BaseModel):
    items: List[RemoteOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
