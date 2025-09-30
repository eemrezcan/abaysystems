#app/schemas/project.py

from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import date, datetime

from app.schemas.customer import CustomerOut
from app.schemas.catalog import RemoteOut  # 🆕 kumanda detayını göstermek için

# --- Ortak PDF bayrakları şeması ---
class PdfFlags(BaseModel):
    camCiktisi: bool = True
    profilAksesuarCiktisi: bool = True
    boyaCiktisi: bool = True
    siparisCiktisi: bool = True
    optimizasyonDetayliCiktisi: bool = True
    optimizasyonDetaysizCiktisi: bool = True

# ----------------------------------------
# Sub-models for project system contents
# ----------------------------------------
class ProfileInProject(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    total_weight_kg: float
    order_index: Optional[int] = None
    # NEW
    is_painted: bool = False
    pdf: Optional[PdfFlags] = None


class GlassInProject(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    area_m2: float
    order_index: Optional[int] = None
    pdf: Optional[PdfFlags] = None


class MaterialInProject(BaseModel):
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None
    # ✅ YENİ ALANLAR:
    type: Optional[str] = None           # DB: String(50), nullable=True
    piece_length_mm: Optional[int] = None
    unit_price: Optional[float] = None   # 💲 proje sistemindeki malzeme birim fiyat snapshot
    order_index: Optional[int] = None
    pdf: Optional[PdfFlags] = None

# 🆕 Kumanda (Remote) — System içinde
class RemoteInProject(BaseModel):
    remote_id: UUID
    count: int
    order_index: Optional[int] = None
    unit_price: Optional[float] = None  # proje anındaki birim fiyat snapshotu (opsiyonel)
    pdf: Optional[PdfFlags] = None

class ProjectPricesUpdate(BaseModel):
    press_price: Optional[float] = None
    painted_price: Optional[float] = None
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
    remotes: List[RemoteInProject] = Field(default_factory=list)  # 🆕

class ExtraRequirement(BaseModel): #materyal extra kısmı class ProjectExtraMaterial(Base): kısmı
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None
    unit_price: Optional[float] = None   # 💲 proje geneli ekstra malzeme birim fiyat snapshot
    pdf: Optional[PdfFlags] = None

class ExtraProfileIn(BaseModel):
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    # NEW
    is_painted: Optional[bool] = False
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None


class ExtraGlassIn(BaseModel):
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None


# 🆕 Proje geneli ekstra kumanda
class ExtraRemoteIn(BaseModel):
    remote_id: UUID
    count: int
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

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
    extra_remotes: List[ExtraRemoteIn] = Field(default_factory=list)  # 🆕

# ----------------------------------------
# Project Creation and Output
# ----------------------------------------
class ProjectMeta(BaseModel):
    customer_id: UUID
    project_name: str
    created_by: UUID

class ProjectCreate(ProjectMeta):
    """Payload for creating a new Project (meta only)"""
    # 🆕 NEW (opsiyonel, üst bilgi fiyat alanları)
    press_price: Optional[float] = None
    painted_price: Optional[float] = None

    # 🆕 NEW (frontend POST’ta gönderecek)
    is_teklif: Optional[bool] = True

    # 🔸 NOT: paint/glass/production status alanları backend’de default "durum belirtilmedi" olacak.

class ProjectUpdate(BaseModel):
    """Projeyi güncellemek için opsiyonel alanlar."""
    project_number: Optional[int] = Field(
        None, ge=0, description="Proje kodunun SAYI kısmı (sadece rakam)."
    )
    customer_id: Optional[UUID]
    project_name: Optional[str]
    profile_color_id: Optional[UUID] = Field(None, description="Yeni profil rengi ID")
    glass_color_id: Optional[UUID] = Field(None, description="Yeni cam rengi ID")
    created_at: Optional[datetime] = None
    press_price: Optional[float] = None
    painted_price: Optional[float] = None

    # 🆕 NEW — PUT ile değişecek alanlar
    is_teklif: Optional[bool] = None
    paint_status: Optional[str] = None
    glass_status: Optional[str] = None
    production_status: Optional[str] = None
    # 🔸 NOT: approval_date’i burada expose ETMİYORUZ (kurala göre backend set edecek)

    class Config:
        orm_mode = True


class ProjectCodeNumberUpdate(BaseModel):
    number: int = Field(..., ge=0, description="Proje kodunun SAYI kısmı (sadece rakam).")


class ProjectOut(ProjectMeta):
    id: UUID
    project_kodu: str = Field(
        ..., description="Otomatik üretilen proje kodu, format: TALU-{sayi}, sayi 10000'den başlar"
    )
    created_at: datetime
    press_price: Optional[float] = None
    painted_price: Optional[float] = None

    # 🆕 NEW — frontend’in görmek istediği alanlar
    is_teklif: bool
    paint_status: str
    glass_status: str
    production_status: str
    approval_date: Optional[datetime] = None   # <- datetime oldu

    class Config:
        orm_mode = True


class ProjectPageOut(BaseModel):
    items: List[ProjectOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
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
    unit_price: Optional[float]
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
    unit_price: Optional[float] = None   # katalogdaki (default) birim fiyat
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ----------------------------------------
# Detailed “extra” modeller
# ----------------------------------------
class ExtraProfileDetailed(BaseModel):
    id: UUID                              # 🆕 id eklendi
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    is_painted: bool
    unit_price: Optional[float] = None
    profile: ProfileOut
    pdf: PdfFlags

    class Config:
        orm_mode = True


class ExtraGlassDetailed(BaseModel):
    id: UUID                              # 🆕 id eklendi
    project_extra_glass_id: UUID  # alias
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    unit_price: Optional[float] = None
    glass_type: GlassTypeOut
    # 🆕 Cam rengi
    glass_color_id: Optional[UUID] = None
    glass_color: Optional['ColorOut'] = None
    pdf: PdfFlags

    class Config:
        orm_mode = True


class ExtraMaterialDetailed(BaseModel):    # 🆕 yeni
    id: UUID
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None
    unit_price: Optional[float] = None
    material: OtherMaterialOut
    pdf: PdfFlags

    class Config:
        orm_mode = True


# 🆕 Extra Remote (detay)
class ExtraRemoteDetailed(BaseModel):
    id: UUID                              # 🆕 id eklendi
    remote_id: UUID
    count: int
    unit_price: Optional[float] = None
    remote: RemoteOut
    pdf: PdfFlags

    class Config:
        orm_mode = True


#-------------------------------------------
class SystemBasicOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProfileInProjectOut(ProfileInProject):
    profile: ProfileOut
    pdf: PdfFlags


    class Config:
        orm_mode = True

class GlassInProjectOut(GlassInProject):
    # ✅ Bu ID, ProjectSystemGlass tablosundaki satırın kimliğidir
    id: UUID

    glass_type: GlassTypeOut
    # (Opsiyonel) mevcut renk ID’si — sadece response için
    glass_color_id: Optional[UUID] = None
    # (Opsiyonel) renk objesi
    glass_color: Optional['ColorOut'] = None
    pdf: PdfFlags

    class Config:
        orm_mode = True



class MaterialInProjectOut(MaterialInProject):
    material: OtherMaterialOut
    pdf: PdfFlags

    class Config:
        orm_mode = True

# 🆕 Remote in System (detaylı)
class RemoteInProjectOut(RemoteInProject):
    remote: RemoteOut
    pdf: PdfFlags

    class Config:
        orm_mode = True

class SystemInProjectOut(BaseModel):
    project_system_id: UUID
    system_variant_id: UUID
    name: str
    system: SystemBasicOut
    width_mm: float
    height_mm: float
    quantity: int
    profiles: List[ProfileInProjectOut]
    glasses: List[GlassInProjectOut]
    materials: List[MaterialInProjectOut]
    remotes: List[RemoteInProjectOut]  # 🆕

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
    customer: CustomerOut
    profile_color: Optional[ColorOut] = None
    glass_color: Optional[ColorOut] = None
    systems: List[SystemInProjectOut]
    # ⬇️ Değişiklik: MaterialInProjectOut yerine ExtraMaterialDetailed
    extra_requirements: List[ExtraMaterialDetailed] = Field(default_factory=list)
    extra_profiles: List[ExtraProfileDetailed] = Field(default_factory=list)
    extra_glasses:  List[ExtraGlassDetailed] = Field(default_factory=list)
    extra_remotes:  List[ExtraRemoteDetailed] = Field(default_factory=list)
    press_price: Optional[float] = None
    painted_price: Optional[float] = None

    class Config:
        orm_mode = True


class ProjectCodeUpdate(BaseModel):
    project_kodu: str = Field(
        ..., 
        min_length=6, 
        max_length=50,
        description="Yeni proje kodu, örn: TALU-12345"
    )

# --- Extra Profile ---
class ProjectExtraProfileCreate(BaseModel):
    project_id: UUID
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    # NEW
    is_painted: Optional[bool] = False
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraProfileUpdate(BaseModel):
    cut_length_mm: Optional[float] = None
    cut_count: Optional[int] = None
    # NEW
    is_painted: Optional[bool] = None
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraProfileOut(BaseModel):
    id: UUID
    project_id: UUID
    profile_id: UUID
    cut_length_mm: float
    cut_count: int
    # NEW
    is_painted: bool
    unit_price: Optional[float] = None
    created_at: datetime
    pdf: PdfFlags

    class Config:
        orm_mode = True

# --- Extra Glass ---
class ProjectExtraGlassCreate(BaseModel):
    project_id: UUID
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None


class ProjectExtraGlassUpdate(BaseModel):
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    count: Optional[int] = None
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None


class ProjectExtraGlassOut(BaseModel):
    id: UUID
    project_id: UUID
    glass_type_id: UUID
    width_mm: float
    height_mm: float
    count: int
    area_m2: Optional[float]
    unit_price: Optional[float] = None
    created_at: datetime
    # 🆕 Cam rengi
    glass_color_id: Optional[UUID] = None
    glass_color: Optional['ColorOut'] = None
    pdf: PdfFlags

    class Config:
        orm_mode = True


#  metaryal EKLE ÇIKART SİL ---------------------------------------
class ProjectExtraMaterialCreate(BaseModel):
    project_id: UUID
    material_id: UUID
    count: int
    cut_length_mm: Optional[float] = None
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraMaterialUpdate(BaseModel):
    count: Optional[int] = None
    cut_length_mm: Optional[float] = None
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraMaterialOut(BaseModel):
    id: UUID
    project_id: UUID
    material_id: UUID
    count: int
    cut_length_mm: Optional[float]
    unit_price: Optional[float] = None
    created_at: datetime
    pdf: PdfFlags

    class Config:
        orm_mode = True

# 🆕 KUMANDA EKSTRA EKLE/ÇIKART/SİL --------------------------------
class ProjectExtraRemoteCreate(BaseModel):
    project_id: UUID
    remote_id: UUID
    count: int
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraRemoteUpdate(BaseModel):
    count: Optional[int] = None
    unit_price: Optional[float] = None
    pdf: Optional[PdfFlags] = None

class ProjectExtraRemoteOut(BaseModel):
    id: UUID
    project_id: UUID
    remote_id: UUID
    count: int
    unit_price: Optional[float] = None
    created_at: datetime
    pdf: PdfFlags

    class Config:
        orm_mode = True


# --- Pydantic forward refs fix ---
try:
    GlassInProjectOut.update_forward_refs(ColorOut=ColorOut)
    ExtraGlassDetailed.update_forward_refs(ColorOut=ColorOut)
    ProjectExtraGlassOut.update_forward_refs(ColorOut=ColorOut)
except NameError:
    # Eğer modül import sırası nedeniyle bir şeyler daha erken okunuyorsa sessizce geç
    pass
