from sqlalchemy.orm import Session

from app.models.app_user import AppUser

from typing import Optional, Tuple, List

from sqlalchemy import or_

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

def get_user_by_email(db: Session, email: str) -> Optional[AppUser]:
    return db.query(AppUser).filter(AppUser.email == email, AppUser.is_deleted == False).first()

def get_dealers_page(
    db: Session,
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[AppUser], int]:
    """
    Admin için bayi (dealer) listesi:
    - is_deleted=False
    - role='dealer'
    - q varsa name/email/city içinde ilike
    - total (count) + items (limit/offset)
    """
    base_q = db.query(AppUser).filter(
        AppUser.role == "dealer",
        AppUser.is_deleted == False,
    )

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(
            or_(
                AppUser.name.ilike(like),
                AppUser.email.ilike(like),
                AppUser.city.ilike(like),
            )
        )

    total = base_q.order_by(None).count()

    items = (
        base_q.order_by(AppUser.created_at.desc())
              .offset(offset)
              .limit(limit)
              .all()
    )

    return items, total