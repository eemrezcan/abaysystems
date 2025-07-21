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

class SystemCreate(SystemBase):
    """Fields for creating a new System"""
    pass

class SystemUpdate(BaseModel):
    """Fields for updating an existing System"""
    name: Optional[str]
    description: Optional[str]

class SystemOut(SystemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ——————————————————————
# SystemVariant CRUD Schemas —
class SystemVariantBase(BaseModel):
    system_id: UUID
    name: str = Field(..., min_length=1)
    color_options: Optional[List[str]] = Field(
        None,
        description="Renk seçenekleri listesi"
    )

    class Config:
        orm_mode = True

class SystemVariantCreate(SystemVariantBase):
    """Fields for creating a System Variant"""
    pass

class SystemVariantUpdate(BaseModel):
    """Fields for updating a System Variant"""
    name: Optional[str]
    color_options: Optional[List[str]]

    class Config:
        orm_mode = True

class SystemVariantOut(SystemVariantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ——————————————————————
# Combined System & Variant & Glass create schema
class GlassConfig(BaseModel):
    glass_type_id: UUID
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)

class VariantConfig(BaseModel):
    name: str = Field(..., min_length=1)
    color_options: Optional[List[str]] = []

class SystemFullCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    variant: VariantConfig
    glass_configs: Optional[List[GlassConfig]] = []

# ——————————————————————
# Template CRUD Schemas — SystemProfileTemplate —
class SystemProfileTemplateBase(BaseModel):
    system_variant_id: UUID
    profile_id: UUID
    formula_cut_length: str = Field(..., min_length=1)
    formula_cut_count: str = Field(..., min_length=1)

class SystemProfileTemplateCreate(SystemProfileTemplateBase):
    pass

class SystemProfileTemplateUpdate(BaseModel):
    formula_cut_length: str = Field(..., min_length=1)
    formula_cut_count: str = Field(..., min_length=1)

class SystemProfileTemplateOut(SystemProfileTemplateBase):
    id: UUID
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
    pass

class SystemGlassTemplateUpdate(BaseModel):
    formula_width: str = Field(..., min_length=1)
    formula_height: str = Field(..., min_length=1)
    formula_count: str = Field(..., min_length=1)

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

class SystemMaterialTemplateCreate(SystemMaterialTemplateBase):
    pass

class SystemMaterialTemplateUpdate(BaseModel):
    formula_quantity: str = Field(..., min_length=1)

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

    class Config:
        orm_mode = True

class GlassTemplateOut(BaseModel):
    glass_type_id: UUID
    formula_width: str
    formula_height: str
    formula_count: str

    class Config:
        orm_mode = True

class MaterialTemplateOut(BaseModel):
    material_id: UUID
    formula_quantity: str

    class Config:
        orm_mode = True

class SystemTemplatesOut(BaseModel):
    profileTemplates: List[ProfileTemplateOut]
    glassTemplates: List[GlassTemplateOut]
    materialTemplates: List[MaterialTemplateOut]

    class Config:
        orm_mode = True
