# app/crud/system_variant.py

from uuid import uuid4, UUID
from sqlalchemy.orm import Session

# Model SystemVariant is defined in app/models/system.py
from app.models.system import SystemVariant
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
