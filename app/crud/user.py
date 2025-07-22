from sqlalchemy.orm import Session

from app.models.app_user import AppUser

from uuid import UUID

def get_user_by_username(db: Session, username: str) -> AppUser | None:
    """
    Verilen username değerine sahip AppUser kaydını döner, yoksa None.
    """
    return db.query(AppUser).filter(AppUser.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> AppUser | None:
    """
    Verilen UUID string’ine karşılık gelen AppUser kaydını döner.
    """
    return db.query(AppUser).filter(AppUser.id == user_id).first()