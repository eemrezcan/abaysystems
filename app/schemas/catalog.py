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

class ProfileOut(ProfileBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# ------- GlassType
class GlassTypeBase(BaseModel):
    cam_isim: str = Field(..., min_length=1)
    thickness_mm: float
    # birim_agirlik alanı kaldırıldı

class GlassTypeCreate(GlassTypeBase):
    pass

class GlassTypeOut(GlassTypeBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# ------- OtherMaterial
class OtherMaterialBase(BaseModel):
    diger_malzeme_isim: str = Field(..., min_length=1)
    birim: str = Field(..., min_length=1)
    birim_agirlik: float
    hesaplama_turu: Optional[str]

class OtherMaterialCreate(OtherMaterialBase):
    pass

class OtherMaterialOut(OtherMaterialBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
