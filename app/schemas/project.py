from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import date, datetime

# ----------------------------------------
# Sub-models for project system contents
# ----------------------------------------
class ProfileInProject(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    total_weight_kg: float

class GlassInProject(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    area_m2: float

class MaterialInProject(BaseModel):
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None

# ----------------------------------------
# SystemRequirement and ExtraRequirement
# ----------------------------------------
class SystemRequirement(BaseModel):
    system_variant_id: UUID
    width_mm: float
    height_mm: float
    quantity: int
    profiles: List[ProfileInProject] = Field(default_factory=list)
    glasses: List[GlassInProject] = Field(default_factory=list)
    materials: List[MaterialInProject] = Field(default_factory=list)

class ExtraRequirement(BaseModel):
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None

class ExtraProfileIn(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int


class ExtraGlassIn(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int


# ----------------------------------------
# Main ProjectSystemsUpdate schema
# (önceki tek endpoint yapısı)
# ----------------------------------------
class ProjectSystemsUpdate(BaseModel):
    systems: List[SystemRequirement]
    extra_requirements: List[ExtraRequirement] = Field(default_factory=list)

    class Config:
        orm_mode = True

# ----------------------------------------
# Bölünmüş payload şemaları
# (yeni endpoint yapıları için)
# ----------------------------------------
class ProjectSystemRequirementIn(BaseModel):
    systems: List[SystemRequirement]

class ProjectExtraRequirementIn(BaseModel):
    extra_requirements: List[ExtraRequirement] = Field(default_factory=list)
    extra_profiles: List[ExtraProfileIn] = Field(default_factory=list)
    extra_glasses: List[ExtraGlassIn] = Field(default_factory=list)


# ----------------------------------------
# Project Creation and Output
# ----------------------------------------
class ProjectMeta(BaseModel):
    customer_id: UUID
    project_name: str
    created_by: UUID

class ProjectCreate(ProjectMeta):
    """Payload for creating a new Project (meta only)"""
    pass

class ProjectUpdate(BaseModel):
    """Projeyi güncellemek için opsiyonel alanlar."""
    customer_id: Optional[UUID]
    project_name: Optional[str]
    created_by: Optional[UUID]

    class Config:
        orm_mode = True

class ProjectOut(ProjectMeta):
    id: UUID
    project_kodu: str = Field(
        ..., 
        description="Otomatik üretilen proje kodu, format: TALU-{sayi}, sayi 10000'den başlar"
    )
    created_at: datetime

    class Config:
        orm_mode = True

# ----------------------------------------
# Detailed Response Models for GET /requirements-detailed
# ----------------------------------------
class ProfileOut(BaseModel):
    id: UUID
    profil_kodu: str
    profil_isim: str
    profil_kesit_fotograf: Optional[str]
    birim_agirlik: float
    boy_uzunluk: float
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
# ----------------------------------------
# Detailed “extra” modeller
# ----------------------------------------
class ExtraProfileDetailed(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    profile: ProfileOut

    class Config:
        orm_mode = True


class ExtraGlassDetailed(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    glass_type: GlassTypeOut

    class Config:
        orm_mode = True
#-------------------------------------------
class SystemBasicOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProfileInProjectOut(ProfileInProject):
    profile: ProfileOut

    class Config:
        orm_mode = True

class GlassInProjectOut(GlassInProject):
    glass_type: GlassTypeOut

    class Config:
        orm_mode = True

class MaterialInProjectOut(MaterialInProject):
    material: OtherMaterialOut

    class Config:
        orm_mode = True

class SystemInProjectOut(BaseModel):
    system_variant_id: UUID
    name: str
    system: SystemBasicOut
    width_mm: float
    height_mm: float
    quantity: int
    profiles: List[ProfileInProjectOut]
    glasses: List[GlassInProjectOut]
    materials: List[MaterialInProjectOut]

    class Config:
        orm_mode = True

class ColorOut(BaseModel):
    id: UUID
    name: str
    type: str
    unit_cost: float

    class Config:
        orm_mode = True

class ProjectColorUpdate(BaseModel):
    profile_color_id: Optional[UUID] = None
    glass_color_id: Optional[UUID] = None


class ProjectRequirementsDetailedOut(BaseModel):
    id: UUID
    profile_color: Optional[ColorOut] = None
    glass_color: Optional[ColorOut] = None
    systems: List[SystemInProjectOut]
    extra_requirements: List[MaterialInProjectOut] = Field(default_factory=list)
    extra_profiles: List[ExtraProfileDetailed] = Field(default_factory=list)
    extra_glasses:  List[ExtraGlassDetailed] = Field(default_factory=list)      
    class Config:
        orm_mode = True

class ProjectCodeUpdate(BaseModel):
    project_kodu: str = Field(
        ..., 
        min_length=6, 
        max_length=50,
        description="Yeni proje kodu, örn: TALU-12345"
    )
#  EKSTRA PROFİL EKLE ÇIKART DÜZENLE  ------------------------
class ProjectExtraProfileCreate(BaseModel):
    project_id: UUID
    profile_id: UUID
    cut_length_mm: float
    cut_count: int

class ProjectExtraProfileUpdate(BaseModel):
    cut_length_mm: Optional[float] = None
    cut_count: Optional[int] = None

class ProjectExtraProfileOut(BaseModel):
    id: UUID
    project_id: UUID
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    created_at: datetime

    class Config:
        orm_mode = True

#  CAM EKLE ÇIKART SİL ---------------------------------------

class ProjectExtraGlassCreate(BaseModel):
    project_id: UUID
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int

class ProjectExtraGlassUpdate(BaseModel):
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    count: Optional[int] = None

class ProjectExtraGlassOut(BaseModel):
    id: UUID
    project_id: UUID
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    area_m2: Optional[float]
    created_at: datetime

    class Config:
        orm_mode = True

#  metaryal EKLE ÇIKART SİL ---------------------------------------

class ProjectExtraMaterialCreate(BaseModel):
    project_id: UUID
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None

class ProjectExtraMaterialUpdate(BaseModel):
    count: Optional[int] = None
    cut_length_mm: Optional[float] = None

class ProjectExtraMaterialOut(BaseModel):
    id: UUID
    project_id: UUID
    material_id: UUID
    count: int
    cut_length_mm: Optional[float]
    created_at: datetime

    class Config:
        orm_mode = True