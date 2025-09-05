# app/crud/dealer_profile_picture.py
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.dealer_profile_picture import DealerProfilePicture

def get_by_user_id(db: Session, user_id: UUID) -> Optional[DealerProfilePicture]:
    return (
        db.query(DealerProfilePicture)
        .filter(DealerProfilePicture.user_id == user_id)
        .first()
    )

def create(db: Session, user_id: UUID, image_url: str) -> DealerProfilePicture:
    obj = DealerProfilePicture(user_id=user_id, image_url=image_url)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_url(db: Session, obj: DealerProfilePicture, image_url: str) -> DealerProfilePicture:
    obj.image_url = image_url
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, obj: DealerProfilePicture) -> None:
    db.delete(obj)
    db.commit()
