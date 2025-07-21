# app/schemas/project.py

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
    color: str
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

# ----------------------------------------
# Main ProjectSystemsUpdate schema
# ----------------------------------------
class ProjectSystemsUpdate(BaseModel):
    systems: List[SystemRequirement]
    extra_requirements: List[ExtraRequirement] = Field(default_factory=list)

    class Config:
        orm_mode = True

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
        description="Otomatik üretilen proje kodu, format: TALU-{sayı}, sayı 10000'den başlar"
    )
    created_at: datetime

    class Config:
        orm_mode = True
