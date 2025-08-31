# app/crud/system_variant.py

from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from typing import Optional, Tuple, List   # 🟢
from sqlalchemy import or_                 # 🟢 q filtresi için

# Model SystemVariant is defined in app/models/system.py
from app.models.system import System, SystemVariant
from app.schemas.system import SystemVariantCreate, SystemVariantUpdate, SystemVariantOut

# ————— SystemVariant CRUD —————

def create_system_variant(db: Session, payload: SystemVariantCreate) -> SystemVariant:
    """
    Create a new SystemVariant record and return it.
    """
    obj = SystemVariant(id=uuid4(), **payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_system_variants(db: Session) -> list[SystemVariant]:
    """List all system variants."""
    return db.query(SystemVariant).all()

def get_system_variants_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: Optional[int],   # 🟢 int -> Optional[int]
    offset: int,
) -> Tuple[List[SystemVariant], int]:
    """
    Tüm varyantlar için sayfalama:
    - SystemVariant.is_deleted=False ve System.is_deleted=False
    - admin değilse: her ikisi de is_published=True
    - q varsa: variant adı veya system adı içinde ilike
    """
    base_q = (
        db.query(SystemVariant)
        .join(System, SystemVariant.system_id == System.id)
        .filter(SystemVariant.is_deleted == False, System.is_deleted == False)
    )

    if not is_admin:
        base_q = base_q.filter(SystemVariant.is_published == True, System.is_published == True)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(or_(SystemVariant.name.ilike(like), System.name.ilike(like)))

    total = base_q.order_by(None).count()

    # 🟢 "all" modunda (limit=None) LIMIT/OFFSET uygulama
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
    limit: Optional[int],   # 🟢 int -> Optional[int]
    offset: int,
) -> Tuple[List[SystemVariant], int]:
    """
    Belirli bir sistem için varyantları sayfalı döndürür.
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

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(SystemVariant.name.ilike(like))

    total = base_q.order_by(None).count()

    # 🟢 "all" modunda (limit=None) LIMIT/OFFSET uygulama
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


# ————— New: fetch variants by system —————

def get_variants_for_system(db: Session, system_id: UUID) -> list[SystemVariant]:
    """
    Verilen system_id'ye ait tüm SystemVariant kayıtlarını döner.
    """
    return db.query(SystemVariant).filter(SystemVariant.system_id == system_id).all()
