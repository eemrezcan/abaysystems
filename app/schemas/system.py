from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# ——————————————————————
# System CRUD Schemas
# — System entity —
class SystemBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    photo_url: Optional[str] = None

class SystemCreate(SystemBase):
    """Fields for creating a new System"""
    pass

class SystemUpdate(BaseModel):
    """Fields for updating an existing System"""
    name: Optional[str] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None
    # ✅ publish/unpublish için
    is_published: Optional[bool] = None

class SystemOut(SystemBase):
    id: UUID
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # ✅ publish durumu
    is_published: bool

    class Config:
        orm_mode = True

# ——————————————————————
# SystemVariant CRUD Schemas —
class SystemVariantBase(BaseModel):
    system_id: UUID
    name: str = Field(..., min_length=1)
    photo_url: Optional[str] = None

    class Config:
        orm_mode = True

class SystemVariantCreate(SystemVariantBase):
    """Fields for creating a System Variant"""
    pass

class SystemVariantUpdate(BaseModel):
    """Fields for updating a System Variant"""
    name: Optional[str] = None
    photo_url: Optional[str] = None
    # ✅ publish/unpublish için
    is_published: Optional[bool] = None

    class Config:
        orm_mode = True

class SystemVariantOut(SystemVariantBase):
    id: UUID
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # ✅ publish durumu
    is_published: bool

    class Config:
        orm_mode = True


class SystemPageOut(BaseModel):
    items: List[SystemOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

class SystemVariantPageOut(BaseModel):
    items: List[SystemVariantOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
# ——————————————————————
# Combined System & Variant & Glass create schema
class GlassConfig(BaseModel):
    glass_type_id: UUID
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)

class VariantConfig(BaseModel):
    name: str = Field(..., min_length=1)
    photo_url: Optional[str] = None

class SystemFullCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    photo_url: Optional[str] = None
    variant: VariantConfig
    glass_configs: Optional[List[GlassConfig]] = []

# ——————————————————————
# Katalog Nesneleri: Profil, Cam, Malzeme
class ProfileOut(BaseModel):
    id: UUID
    profil_kodu: str
    profil_isim: str
    profil_kesit_fotograf: Optional[str]
    birim_agirlik: float
    boy_uzunluk: float
    unit_price: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class GlassTypeOut(BaseModel):
    id: UUID
    cam_isim: str
    thickness_mm: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OtherMaterialOut(BaseModel):
    id: UUID
    diger_malzeme_isim: str
    birim: str
    birim_agirlik: float
    hesaplama_turu: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SystemBasicOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ——————————————————————
# Template CRUD Schemas — SystemProfileTemplate —
class SystemProfileTemplateBase(BaseModel):
    system_variant_id: UUID
    profile_id: UUID
    formula_cut_length: str = Field(..., min_length=1)
    formula_cut_count: str = Field(..., min_length=1)

class SystemProfileTemplateCreate(SystemProfileTemplateBase):
    order_index: Optional[int] = None

class SystemProfileTemplateUpdate(BaseModel):
    formula_cut_length: str = Field(..., min_length=1)
    formula_cut_count: str = Field(..., min_length=1)
    order_index: Optional[int] = None

class SystemProfileTemplateOut(SystemProfileTemplateBase):
    id: UUID
    order_index: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True

# — SystemGlassTemplate —
class SystemGlassTemplateBase(BaseModel):
    system_variant_id: UUID
    glass_type_id: UUID
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)

class SystemGlassTemplateCreate(SystemGlassTemplateBase):
    order_index: Optional[int] = None

class SystemGlassTemplateUpdate(BaseModel):
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)
    order_index: Optional[int] = None

class SystemGlassTemplateOut(SystemGlassTemplateBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# — SystemMaterialTemplate —
class SystemMaterialTemplateBase(BaseModel):
    system_variant_id: UUID
    material_id: UUID
    formula_quantity: str = Field(..., min_length=1)
    formula_cut_length: Optional[str] = None

class SystemMaterialTemplateCreate(SystemMaterialTemplateBase):
    order_index: Optional[int] = None

class SystemMaterialTemplateUpdate(BaseModel):
    formula_quantity: str = Field(..., min_length=1)
    formula_cut_length: Optional[str] = None
    order_index: Optional[int] = None

class SystemMaterialTemplateOut(SystemMaterialTemplateBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# ——————————————————————
# Toplu GET için “view” Şemaları
class ProfileTemplateOut(BaseModel):
    profile_id: UUID
    formula_cut_length: str
    formula_cut_count: str
    order_index: Optional[int] = None
    profile: ProfileOut  # EKLENDİ

    class Config:
        orm_mode = True

class GlassTemplateOut(BaseModel):
    glass_type_id: UUID
    formula_width: str
    formula_height: str
    formula_count: str
    order_index: Optional[int] = None
    glass_type: GlassTypeOut  # EKLENDİ

    class Config:
        orm_mode = True

class MaterialTemplateOut(BaseModel):
    material_id: UUID
    formula_quantity: str
    formula_cut_length: str
    order_index: Optional[int] = None
    material: OtherMaterialOut  # EKLENDİ

    class Config:
        orm_mode = True

class SystemTemplatesOut(BaseModel):
    profileTemplates: List[ProfileTemplateOut]
    glassTemplates: List[GlassTemplateOut]
    materialTemplates: List[MaterialTemplateOut]

    class Config:
        orm_mode = True

class SystemVariantDetailOut(BaseModel):
    id: UUID
    name: str
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    system: SystemBasicOut
    profile_templates: List[ProfileTemplateOut]
    glass_templates: List[GlassTemplateOut]
    material_templates: List[MaterialTemplateOut]

    class Config:
        orm_mode = True

# ——————————————————————
# New: Bulk-create a SystemVariant with its templates
class ProfileTemplateIn(BaseModel):
    profile_id: UUID
    formula_cut_length: str = Field(..., min_length=1)
    formula_cut_count: str = Field(..., min_length=1)
    order_index: Optional[int] = None

class GlassTemplateIn(BaseModel):
    glass_type_id: UUID
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)
    order_index: Optional[int] = None

class MaterialTemplateIn(BaseModel):
    material_id: UUID
    formula_quantity: str = Field(..., min_length=1)
    formula_cut_length: Optional[str] = None
    order_index: Optional[int] = None

class SystemVariantCreateWithTemplates(BaseModel):
    system_id: UUID = Field(..., alias="systemId")
    name: str = Field(..., min_length=1)
    profile_templates: List[ProfileTemplateIn] = Field(default_factory=list)
    glass_templates: List[GlassTemplateIn] = Field(default_factory=list)
    material_templates: List[MaterialTemplateIn] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

# ——————————————————————
# New: Update a SystemVariant + templates
class SystemVariantUpdateWithTemplates(BaseModel):
    name: Optional[str] = None
    profile_templates: List[ProfileTemplateIn] = Field(default_factory=list)
    glass_templates: List[GlassTemplateIn] = Field(default_factory=list)
    material_templates: List[MaterialTemplateIn] = Field(default_factory=list)

    class Config:
        orm_mode = True
