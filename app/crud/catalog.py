# app/crud/catalog.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.profile        import Profile
from app.models.glass_type     import GlassType
from app.models.other_material import OtherMaterial
from app.schemas.catalog       import (
    ProfileCreate,
    GlassTypeCreate,
    OtherMaterialCreate
)

# ----- PROFILE CRUD (unchanged) -----
def get_profile_by_code(db: Session, code: str) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.profil_kodu == code).first()


def create_profile(db: Session, payload: ProfileCreate) -> Profile:
    obj = Profile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_profiles(db: Session) -> List[Profile]:
    return db.query(Profile).all()


def get_profile(db: Session, profile_id: UUID) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.id == profile_id).first()


def update_profile(db: Session, profile_id: UUID, payload: ProfileCreate) -> Optional[Profile]:
    obj = get_profile(db, profile_id)
    if not obj:
        return None
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_profile(db: Session, profile_id: UUID) -> None:
    db.query(Profile).filter(Profile.id == profile_id).delete()
    db.commit()


# ----- GLASS TYPE CRUD -----
# Note: 'birim_agirlik' field removed from model and schema

def create_glass_type(db: Session, payload: GlassTypeCreate) -> GlassType:
    obj = GlassType(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_glass_types(db: Session) -> List[GlassType]:
    return db.query(GlassType).all()


def get_glass_type(db: Session, glass_type_id: UUID) -> Optional[GlassType]:
    return db.query(GlassType).filter(GlassType.id == glass_type_id).first()


def update_glass_type(db: Session, glass_type_id: UUID, payload: GlassTypeCreate) -> Optional[GlassType]:
    obj = get_glass_type(db, glass_type_id)
    if not obj:
        return None
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_glass_type(db: Session, glass_type_id: UUID) -> bool:
    deleted = db.query(GlassType).filter(GlassType.id == glass_type_id).delete()
    db.commit()
    return bool(deleted)


# ----- OTHER MATERIAL CRUD (unchanged) -----
def create_other_material(db: Session, payload: OtherMaterialCreate) -> OtherMaterial:
    obj = OtherMaterial(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_other_materials(db: Session) -> List[OtherMaterial]:
    return db.query(OtherMaterial).all()


def get_other_material(db: Session, material_id: UUID) -> Optional[OtherMaterial]:
    return db.query(OtherMaterial).filter(OtherMaterial.id == material_id).first()


def update_other_material(db: Session, material_id: UUID, payload: OtherMaterialCreate) -> Optional[OtherMaterial]:
    obj = get_other_material(db, material_id)
    if not obj:
        return None
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_other_material(db: Session, material_id: UUID) -> bool:
    deleted = db.query(OtherMaterial).filter(OtherMaterial.id == material_id).delete()
    db.commit()
    return bool(deleted)
