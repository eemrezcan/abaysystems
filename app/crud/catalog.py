import os
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from sqlalchemy import or_
from uuid import UUID

from app.models.profile import Profile
from app.models.glass_type import GlassType
from app.models.other_material import OtherMaterial
from app.schemas.catalog import (
    ProfileCreate,
    ProfileUpdate,
    GlassTypeCreate,
    GlassTypeUpdate,
    OtherMaterialCreate,
)
from app.crud.active import set_active_state  # ✅ is_active toggle helper

from app.models.remote import Remote
from app.schemas.catalog import RemoteCreate


# ----- PROFILE CRUD -----

def get_profile_by_code(db: Session, code: str) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.profil_kodu == code).first()


def create_profile(db: Session, payload: ProfileCreate) -> Profile:
    obj = Profile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_profiles(db: Session) -> List[Profile]:
    return (
        db.query(Profile)
        .filter(Profile.is_deleted == False, Profile.is_active == True)  # noqa: E712
        .order_by(Profile.profil_isim.asc())
        .all()
    )


def get_profile(db: Session, profile_id: UUID) -> Optional[Profile]:
    # Tekil getirirken is_active filtresi uygulanmaz (silinmemiş olması yeterli)
    return (
        db.query(Profile)
        .filter(Profile.id == profile_id, Profile.is_deleted == False)  # noqa: E712
        .first()
    )


def update_profile(db: Session, profile_id: UUID, payload: ProfileUpdate) -> Optional[Profile]:
    obj = get_profile(db, profile_id)
    if not obj:
        return None
    old_code = obj.profil_kodu
    old_photo_path = obj.profil_kesit_fotograf
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    # Profil kodu değişmişse varsa mevcut fotoğrafı yeni ada taşı
    new_code = getattr(obj, "profil_kodu", old_code)
    if (
        old_photo_path
        and new_code
        and old_code != new_code
    ):
        directory = os.path.dirname(old_photo_path) or "."
        _, ext = os.path.splitext(old_photo_path)
        new_photo_path = os.path.join(directory, f"{new_code}{ext}")
        try:
            if os.path.exists(old_photo_path):
                os.rename(old_photo_path, new_photo_path)
                obj.profil_kesit_fotograf = new_photo_path
        except OSError:
            pass
    db.commit()
    db.refresh(obj)
    return obj


def delete_profile(db: Session, profile_id: UUID) -> None:
    db.query(Profile).filter(Profile.id == profile_id).delete()
    db.commit()


# ----- GLASS TYPE CRUD -----

def create_glass_type(db: Session, payload: GlassTypeCreate) -> GlassType:
    obj = GlassType(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_glass_types(db: Session) -> List[GlassType]:
    return (
        db.query(GlassType)
        .filter(GlassType.is_deleted == False, GlassType.is_active == True)  # noqa: E712
        .order_by(GlassType.cam_isim.asc())
        .all()
    )


def get_glass_type(db: Session, glass_type_id: UUID) -> Optional[GlassType]:
    # Tekil getirirken is_active filtresi uygulanmaz (silinmemiş olması yeterli)
    return (
        db.query(GlassType)
        .filter(GlassType.id == glass_type_id, GlassType.is_deleted == False)  # noqa: E712
        .first()
    )


def update_glass_type(db: Session, glass_type_id: UUID, payload: GlassTypeUpdate) -> Optional[GlassType]:
    obj = get_glass_type(db, glass_type_id)
    if not obj:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_glass_type(db: Session, glass_type_id: UUID) -> bool:
    deleted = db.query(GlassType).filter(GlassType.id == glass_type_id).delete()
    db.commit()
    return bool(deleted)


# ----- OTHER MATERIAL CRUD -----

def create_other_material(db: Session, payload: OtherMaterialCreate) -> OtherMaterial:
    obj = OtherMaterial(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_other_materials(db: Session) -> List[OtherMaterial]:
    return (
        db.query(OtherMaterial)
        .filter(OtherMaterial.is_deleted == False, OtherMaterial.is_active == True)  # noqa: E712
        .order_by(OtherMaterial.diger_malzeme_isim.asc())
        .all()
    )


def get_other_material(db: Session, material_id: UUID) -> Optional[OtherMaterial]:
    # Tekil getirirken is_active filtresi uygulanmaz (silinmemiş olması yeterli)
    return (
        db.query(OtherMaterial)
        .filter(OtherMaterial.id == material_id, OtherMaterial.is_deleted == False)  # noqa: E712
        .first()
    )


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
    Liste ucu: her zaman is_deleted = False ve is_active = True
    q varsa profil_isim veya profil_kodu ILIKE ile aranır.
    """
    base_q = db.query(Profile).filter(
        Profile.is_deleted == False,  # noqa: E712
        Profile.is_active == True,    # noqa: E712
    )

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
    Liste ucu: her zaman is_deleted = False ve is_active = True
    q varsa cam_isim ILIKE ile aranır.
    """
    base_q = db.query(GlassType).filter(
        GlassType.is_deleted == False,  # noqa: E712
        GlassType.is_active == True,    # noqa: E712
    )

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
    Liste ucu: her zaman is_deleted = False ve is_active = True
    q varsa diger_malzeme_isim ILIKE ile aranır.
    """
    base_q = db.query(OtherMaterial).filter(
        OtherMaterial.is_deleted == False,  # noqa: E712
        OtherMaterial.is_active == True,    # noqa: E712
    )

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
        kumanda_isim=payload.kumanda_isim,
        price=payload.price,
        kapasite=payload.kapasite,
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
    Liste ucu: her zaman is_deleted = False ve is_active = True
    q varsa kumanda_isim ILIKE ile aranır.
    """
    base_q = db.query(Remote).filter(
        Remote.is_deleted == False,  # noqa: E712
        Remote.is_active == True,    # noqa: E712
    )

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(Remote.kumanda_isim.ilike(like))

    total = base_q.order_by(None).count()
    items = (
        base_q.order_by(Remote.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return items, total


def get_remote(db: Session, remote_id: UUID) -> Optional[Remote]:
    # Tekil getirirken is_active filtresi uygulanmaz (silinmemiş olması yeterli)
    return (
        db.query(Remote)
        .filter(Remote.id == remote_id, Remote.is_deleted == False)  # noqa: E712
        .first()
    )


def update_remote(db: Session, remote_id: UUID, payload: RemoteCreate) -> Optional[Remote]:
    obj = db.query(Remote).filter(Remote.id == remote_id, Remote.is_deleted == False).first()  # noqa: E712
    if not obj:
        return None

    obj.kumanda_isim = payload.kumanda_isim
    obj.price = payload.price
    obj.kapasite = payload.kapasite

    db.commit()
    db.refresh(obj)
    return obj


def delete_remote(db: Session, remote_id: UUID) -> bool:
    """
    Soft delete: is_deleted=True, is_active=False
    """
    obj = db.query(Remote).filter(Remote.id == remote_id, Remote.is_deleted == False).first()  # noqa: E712
    if not obj:
        return False

    obj.is_deleted = True
    obj.is_active = False

    db.commit()
    return True


# ------------------------------
# ✅ is_active toggle helpers
# ------------------------------

def set_profile_active(db: Session, profile_id: UUID, active: bool):
    return set_active_state(db, Profile, profile_id, active)


def set_glass_type_active(db: Session, glass_type_id: UUID, active: bool):
    return set_active_state(db, GlassType, glass_type_id, active)


def set_other_material_active(db: Session, material_id: UUID, active: bool):
    return set_active_state(db, OtherMaterial, material_id, active)


def set_remote_active(db: Session, remote_id: UUID, active: bool):
    return set_active_state(db, Remote, remote_id, active)
