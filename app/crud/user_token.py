# app/crud/user_token.py
from sqlalchemy.orm import Session
from app.models.user_token import UserToken

def invalidate_all(db: Session, user_id, token_type: str) -> int:
    res = db.query(UserToken).filter(
        UserToken.user_id == user_id,
        UserToken.type == token_type,
        UserToken.used_at.is_(None)
    ).delete(synchronize_session=False)
    db.commit()
    return res

def get_active_by_hash(db: Session, token_hash: str, token_type: str) -> UserToken | None:
    return db.query(UserToken).filter(
        UserToken.token_hash == token_hash,
        UserToken.type == token_type,
        UserToken.used_at.is_(None)
    ).first()
