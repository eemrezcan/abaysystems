# app/crud/system.py

from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List
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
    SystemFullCreate,
    SystemVariantCreateWithTemplates,
    SystemVariantUpdateWithTemplates
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

def create_system_variant(db: Session, system_id: UUID, payload: SystemVariantCreate) -> SystemVariant:
    # payload.dict() içinde gelen system_id alanını at, path'ten aldığımızı kullanacağız
    data = payload.dict(by_alias=True, exclude={"system_id"})
    obj = SystemVariant(
        id=uuid4(),
        system_id=system_id,
        **data
    )
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
    # 1) System oluştur
    system = System(
        id=uuid4(),
        name=payload.name,
        description=payload.description,
        photo_url=payload.photo_url  # 👈 EKLENDİ
    )
    db.add(system)
    db.flush()

    # 2) Variant oluştur
    variant_data = payload.variant.dict(by_alias=True)
    variant = SystemVariant(
        id=uuid4(),
        system_id=system.id,
        name=variant_data["name"],
        photo_url=variant_data.get("photo_url"),  # 👈 EKLENDİ
    )
    db.add(variant)
    db.flush()

    # 3) Glass templates ekle
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

    db.commit()
    db.refresh(system)
    return {
        "system": system,
        "variant": variant,
        "glass_templates": payload.glass_configs
    }


def get_system_variant_detail(db: Session, variant_id: UUID) -> Optional[SystemVariant]:
    return (
        db.query(SystemVariant)
        .filter(SystemVariant.id == variant_id)
        .options(
            joinedload(SystemVariant.system),
            joinedload(SystemVariant.profile_templates).joinedload(SystemProfileTemplate.profile),
            joinedload(SystemVariant.glass_templates).joinedload(SystemGlassTemplate.glass_type),
            joinedload(SystemVariant.material_templates).joinedload(SystemMaterialTemplate.material),
        )
        .first()
    )


def create_system_variant_with_templates(
    db: Session,
    payload: SystemVariantCreateWithTemplates
) -> SystemVariant:
    """
    Bir SystemVariant kaydı ve ilişkili profil, cam, malzeme şablonlarını topluca oluşturur.
    """
    # 1) Variant oluştur
    variant = SystemVariant(
        id=uuid4(),
        system_id=payload.system_id,
        name=payload.name
    )
    db.add(variant)
    db.flush()

    # 2) Profile şablonları ekle
    for pt in payload.profile_templates:
        db.add(SystemProfileTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            profile_id=pt.profile_id,
            formula_cut_length=pt.formula_cut_length,
            formula_cut_count=pt.formula_cut_count
        ))

    # 3) Glass şablonları ekle
    for gt in payload.glass_templates:
        db.add(SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            glass_type_id=gt.glass_type_id,
            formula_width=gt.formula_width,
            formula_height=gt.formula_height,
            formula_count=gt.formula_count
        ))

    # 4) Material şablonları ekle
    for mt in payload.material_templates:
        db.add(SystemMaterialTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            material_id=mt.material_id,
            formula_quantity=mt.formula_quantity,
            formula_cut_length=mt.formula_cut_length
        ))

    # 5) Commit ve refresh
    db.commit()
    db.refresh(variant)
    return variant

# ————— Update SystemVariant + all its templates —————
def update_system_variant_with_templates(
    db: Session,
    variant_id: UUID,
    payload: SystemVariantUpdateWithTemplates
) -> SystemVariant:
    # 1) Var olan variant’ı al
    variant = get_system_variant(db, variant_id)
    if not variant:
        raise ValueError("Variant not found")

    # 2) İsim güncelle (gelmişse)
    if payload.name is not None:
        variant.name = payload.name

    # 3) Eski şablonları sil
    db.query(SystemProfileTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.query(SystemGlassTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.query(SystemMaterialTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.flush()

    # 4) Yeni şablonları ekle
    for pt in payload.profile_templates:
        db.add(SystemProfileTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            profile_id=pt.profile_id,
            formula_cut_length=pt.formula_cut_length,
            formula_cut_count=pt.formula_cut_count
        ))
    for gt in payload.glass_templates:
        db.add(SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            glass_type_id=gt.glass_type_id,
            formula_width=gt.formula_width,
            formula_height=gt.formula_height,
            formula_count=gt.formula_count
        ))
    for mt in payload.material_templates:
        db.add(SystemMaterialTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            material_id=mt.material_id,
            formula_quantity=mt.formula_quantity,
            formula_cut_length=mt.formula_cut_length
        ))

    # 5) Commit ve refresh
    db.commit()
    db.refresh(variant)
    return variant

