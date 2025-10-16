# app/crud/system_variant.py

from uuid import uuid4, UUID
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.system import System, SystemVariant
from app.schemas.system import (
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemVariantOut,  # kullanılmıyor ama bırakmak sorun değil
)


# ————— SystemVariant CRUD —————

def create_system_variant(db: Session, payload: SystemVariantCreate) -> SystemVariant:
    """
    Create a new SystemVariant record and return it.
    is_active alanı payload'dan gelebilir.
    """
    obj = SystemVariant(id=uuid4(), **payload.dict(exclude_unset=True))  # ✅ is_active gelebilir
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_system_variants(db: Session) -> List[SystemVariant]:
    """List all system variants."""
    return db.query(SystemVariant).all()


def get_system_variants_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: Optional[int],
    offset: int,
    only_active: Optional[bool] = None,  # ✅ eklendi
) -> Tuple[List[SystemVariant], int]:
    """
    Tüm varyantlar için sayfalama:
    - SystemVariant.is_deleted=False ve System.is_deleted=False
    - admin değilse: her ikisi de is_published=True
    - q varsa: variant adı veya system adı içinde ilike
    - only_active=True ise: hem SystemVariant hem System aktif olmalı
    """
    base_q = (
        db.query(SystemVariant)
        .join(System, SystemVariant.system_id == System.id)
        .filter(SystemVariant.is_deleted == False, System.is_deleted == False)
    )

    if not is_admin:
        base_q = base_q.filter(SystemVariant.is_published == True, System.is_published == True)

    if only_active is True:
        base_q = base_q.filter(SystemVariant.is_active == True, System.is_active == True)  # ✅

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(or_(SystemVariant.name.ilike(like), System.name.ilike(like)))

    total = base_q.order_by(None).count()

    q_items = base_q.order_by(SystemVariant.created_at.desc())
    if limit is None:
        items = q_items.all()
    else:
        items = q_items.offset(offset).limit(limit).all()

    return items, total


def get_variants_for_system_page(
    db: Session,
    system_id: UUID,
    is_admin: bool,
    q: Optional[str],
    limit: Optional[int],
    offset: int,
    only_active: Optional[bool] = None,  # ✅ eklendi
) -> Tuple[List[SystemVariant], int]:
    """
    Belirli bir sistem için varyantları sayfalı döndürür.
    - SystemVariant/System is_deleted=False
    - admin değilse: her ikisi de is_published=True
    - only_active=True ise: hem SystemVariant hem System aktif olmalı
    """
    base_q = (
        db.query(SystemVariant)
        .join(System, SystemVariant.system_id == System.id)
        .filter(
            SystemVariant.system_id == system_id,
            SystemVariant.is_deleted == False,
            System.is_deleted == False,
        )
    )

    if not is_admin:
        base_q = base_q.filter(SystemVariant.is_published == True, System.is_published == True)

    if only_active is True:
        base_q = base_q.filter(SystemVariant.is_active == True, System.is_active == True)  # ✅

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(SystemVariant.name.ilike(like))

    total = base_q.order_by(None).count()

    q_items = base_q.order_by(SystemVariant.created_at.desc())
    if limit is None:
        items = q_items.all()
    else:
        items = q_items.offset(offset).limit(limit).all()

    return items, total


def get_system_variant(db: Session, variant_id: UUID) -> SystemVariant | None:
    """Get a single system variant by ID."""
    return db.query(SystemVariant).filter_by(id=variant_id).first()


def update_system_variant(db: Session, variant_id: UUID, payload: SystemVariantUpdate) -> SystemVariant | None:
    """Update fields of an existing system variant."""
    obj = get_system_variant(db, variant_id)
    if not obj:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_system_variant(db: Session, variant_id: UUID) -> bool:
    """Delete a system variant by ID."""
    deleted = db.query(SystemVariant).filter_by(id=variant_id).delete()
    db.commit()
    return bool(deleted)


# ————— Fetch variants by system —————

def get_variants_for_system(
    db: Session,
    system_id: UUID,
    only_active: Optional[bool] = None,  # ✅ opsiyonel aktif filtresi
) -> List[SystemVariant]:
    """
    Verilen system_id'ye ait tüm SystemVariant kayıtlarını döner.
    only_active=True ise sadece aktif varyantlar.
    """
    q = db.query(SystemVariant).filter(SystemVariant.system_id == system_id)
    if only_active is True:
        q = q.filter(SystemVariant.is_active == True)
    return q.all()
