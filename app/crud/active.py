# app/crud/active.py
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Type

from app.models.glass_type import GlassType
from app.models.profile import Profile
from app.models.remote import Remote
from app.models.other_material import OtherMaterial

CatalogModel = Type[GlassType] | Type[Profile] | Type[Remote] | Type[OtherMaterial]

def set_active_state(db: Session, model: CatalogModel, item_id: UUID, active: bool):
    obj = db.query(model).filter(model.id == item_id, model.is_deleted == False).first()
    if not obj:
        return None
    obj.is_active = active
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
