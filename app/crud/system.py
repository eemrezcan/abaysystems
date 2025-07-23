# app/crud/system.py

from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional
from app.models.system import System, SystemVariant
from app.models.system_profile_template import SystemProfileTemplate
from app.models.system_glass_template import SystemGlassTemplate
from app.models.system_material_template import SystemMaterialTemplate
from app.schemas.system import (
    SystemCreate,
    SystemUpdate,
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemProfileTemplateCreate,
    SystemProfileTemplateUpdate,
    SystemGlassTemplateCreate,
    SystemGlassTemplateUpdate,
    SystemMaterialTemplateCreate,
    SystemMaterialTemplateUpdate,
    SystemFullCreate
)

# ————— System CRUD —————

def create_system(db: Session, payload: SystemCreate) -> System:
    obj = System(id=uuid4(), **payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_systems(db: Session) -> list[System]:
    return db.query(System).all()


def get_system(db: Session, system_id: UUID) -> System | None:
    return db.query(System).filter_by(id=system_id).first()


def update_system(db: Session, system_id: UUID, payload: SystemUpdate) -> System | None:
    obj = get_system(db, system_id)
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_system(db: Session, system_id: UUID) -> bool:
    deleted = db.query(System).filter_by(id=system_id).delete()
    db.commit()
    return bool(deleted)

# ————— SystemVariant CRUD —————

def create_system_variant(db: Session, payload: SystemVariantCreate) -> SystemVariant:
    obj = SystemVariant(id=uuid4(), **payload.dict(by_alias=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_system_variants(db: Session) -> list[SystemVariant]:
    return db.query(SystemVariant).all()


def get_system_variant(db: Session, variant_id: UUID) -> SystemVariant | None:
    return db.query(SystemVariant).filter_by(id=variant_id).first()


def update_system_variant(db: Session, variant_id: UUID, payload: SystemVariantUpdate) -> SystemVariant | None:
    obj = get_system_variant(db, variant_id)
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True, by_alias=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_system_variant(db: Session, variant_id: UUID) -> bool:
    deleted = db.query(SystemVariant).filter_by(id=variant_id).delete()
    db.commit()
    return bool(deleted)

# ————— Template CRUD —————

def create_profile_template(db: Session, payload: SystemProfileTemplateCreate) -> SystemProfileTemplate:
    obj = SystemProfileTemplate(id=uuid4(), **payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_profile_templates(db: Session, variant_id: UUID) -> list[SystemProfileTemplate]:
    return db.query(SystemProfileTemplate).filter_by(system_variant_id=variant_id).all()


def update_profile_template(db: Session, template_id: UUID, payload: SystemProfileTemplateUpdate) -> SystemProfileTemplate | None:
    obj = db.query(SystemProfileTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_profile_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemProfileTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)


def create_glass_template(db: Session, payload: SystemGlassTemplateCreate) -> SystemGlassTemplate:
    obj = SystemGlassTemplate(id=uuid4(), **payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_glass_templates(db: Session, variant_id: UUID) -> list[SystemGlassTemplate]:
    return db.query(SystemGlassTemplate).filter_by(system_variant_id=variant_id).all()


def update_glass_template(db: Session, template_id: UUID, payload: SystemGlassTemplateUpdate) -> SystemGlassTemplate | None:
    obj = db.query(SystemGlassTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_glass_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemGlassTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)


def create_material_template(db: Session, payload: SystemMaterialTemplateCreate) -> SystemMaterialTemplate:
    obj = SystemMaterialTemplate(id=uuid4(), **payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_material_templates(db: Session, variant_id: UUID) -> list[SystemMaterialTemplate]:
    return db.query(SystemMaterialTemplate).filter_by(system_variant_id=variant_id).all()


def update_material_template(db: Session, template_id: UUID, payload: SystemMaterialTemplateUpdate) -> SystemMaterialTemplate | None:
    obj = db.query(SystemMaterialTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_material_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemMaterialTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)

# ————— Combined template fetch —————

def get_system_templates(db: Session, variant_id: UUID):
    profiles = get_profile_templates(db, variant_id)
    glasses = get_glass_templates(db, variant_id)
    materials = get_material_templates(db, variant_id)
    return profiles, glasses, materials

# ————— Combined full creation —————

def create_system_full(db: Session, payload: SystemFullCreate):
    """Tek seferde System + Variant + Glass‐Config yaratır."""
    # 1) System’i yalnızca name/description ile oluştur
    system = System(
        id=uuid4(),
        name=payload.name,
        description=payload.description
    )
    db.add(system)
    db.flush()  # system.id’yi alabilmek için

    # 2) Variant’ı oluştur (alias’lı alanları dict ile alıyoruz)
    variant_data = payload.variant.dict(by_alias=True)
    variant = SystemVariant(
        id=uuid4(),
        system_id=system.id,
        name=variant_data["name"],
        max_width_m=variant_data.get("max_width_mm"),
        max_height_m=variant_data.get("max_height_mm"),
        color_options=variant_data.get("color_options"),
    )
    db.add(variant)
    db.flush()  # variant.id için

    # 3) Glass‐config’leri ekle
    for g in payload.glass_configs or []:
        tpl = SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            glass_type_id=g.glass_type_id,
            formula_width=g.formula_width,
            formula_height=g.formula_height,
            formula_count=g.formula_count
        )
        db.add(tpl)

    # 4) Commit et ve geri döndür
    db.commit()
    db.refresh(system)
    return {
        "system": system,
        "variant": variant,
        "glass_templates": payload.glass_configs  # isterseniz bunları da dönebilirsiniz
    }

def get_system_variant_detail(db: Session, variant_id: UUID) -> Optional[SystemVariant]:
    return (
        db.query(SystemVariant)
        .filter(SystemVariant.id == variant_id)
        .options(
            joinedload(SystemVariant.profile_templates).joinedload(SystemProfileTemplate.profile),
            joinedload(SystemVariant.glass_templates).joinedload(SystemGlassTemplate.glass_type),
            joinedload(SystemVariant.material_templates).joinedload(SystemMaterialTemplate.material),
        )
        .first()
    )
