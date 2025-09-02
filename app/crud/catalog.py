# app/crud/catalog.py

from sqlalchemy.orm import Session
from typing import List, Optional, Tuple  # 🟢 Tuple ekle
from sqlalchemy import or_  
from uuid import UUID

from app.models.profile        import Profile
from app.models.glass_type     import GlassType
from app.models.other_material import OtherMaterial
from app.schemas.catalog       import (
    ProfileCreate,
    GlassTypeCreate,
    OtherMaterialCreate
)

from app.models.remote import Remote
from app.schemas.catalog import RemoteCreate

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



# ------- PROFILE (paginated) -------
def get_profiles_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Profile], int]:
    """
    - is_deleted = False zorunlu
    - admin değilse is_active = True
    - q varsa profil_isim veya profil_kodu içinde arar (ILIKE)
    """
    base_q = db.query(Profile).filter(Profile.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(Profile.is_active == True)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(
            or_(Profile.profil_isim.ilike(like), Profile.profil_kodu.ilike(like))
        )

    total = base_q.order_by(None).count()
    items = (
        base_q.order_by(Profile.profil_isim.asc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total

# ------- GLASS TYPE (paginated) -------
def get_glass_types_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[GlassType], int]:
    """
    - is_deleted = False zorunlu
    - admin değilse is_active = True
    - q varsa cam_isim içinde arar (ILIKE)
    """
    base_q = db.query(GlassType).filter(GlassType.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(GlassType.is_active == True)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(GlassType.cam_isim.ilike(like))

    total = base_q.order_by(None).count()
    items = (
        base_q.order_by(GlassType.cam_isim.asc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total

# ------- OTHER MATERIAL (paginated) -------
def get_other_materials_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[OtherMaterial], int]:
    """
    - is_deleted = False zorunlu
    - admin değilse is_active = True
    - q varsa diger_malzeme_isim içinde arar (ILIKE)
    """
    base_q = db.query(OtherMaterial).filter(OtherMaterial.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(OtherMaterial.is_active == True)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(OtherMaterial.diger_malzeme_isim.ilike(like))

    total = base_q.order_by(None).count()
    items = (
        base_q.order_by(OtherMaterial.diger_malzeme_isim.asc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total



# ---------------------------
# REMOTE (Kumanda) - CRUD
# ---------------------------

def create_remote(db: Session, payload: RemoteCreate) -> Remote:
    obj = Remote(
        kumanda_isim = payload.kumanda_isim,
        price        = payload.price,
        kapasite     = payload.kapasite,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_remotes_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Remote], int]:
    """
    Sayfalı liste:
    - is_deleted = False
    - admin değilse: is_active=True
    - q varsa: kumanda_isim ILIKE %q%
    """
    base_q = db.query(Remote).filter(Remote.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(Remote.is_active == True)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(Remote.kumanda_isim.ilike(like))

    total = base_q.order_by(None).count()

    items = (
        base_q
        .order_by(Remote.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return items, total


def get_remote(db: Session, remote_id: UUID) -> Optional[Remote]:
    return db.query(Remote).filter(Remote.id == remote_id).first()


def update_remote(db: Session, remote_id: UUID, payload: RemoteCreate) -> Optional[Remote]:
    obj = db.query(Remote).filter(Remote.id == remote_id, Remote.is_deleted == False).first()
    if not obj:
        return None

    obj.kumanda_isim = payload.kumanda_isim
    obj.price        = payload.price
    obj.kapasite     = payload.kapasite

    db.commit()
    db.refresh(obj)
    return obj


def delete_remote(db: Session, remote_id: UUID) -> bool:
    """
    Soft delete: is_deleted=True, is_active=False
    """
    obj = db.query(Remote).filter(Remote.id == remote_id, Remote.is_deleted == False).first()
    if not obj:
        return False

    obj.is_deleted = True
    obj.is_active  = False

    db.commit()
    return True
