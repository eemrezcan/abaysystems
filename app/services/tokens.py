# app/services/tokens.py
from __future__ import annotations
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.user_token import UserToken

# Üretilecek token düz metin (kullanıcıya giden) + hash (DB'ye kaydedilen)
def generate_token() -> Tuple[str, str]:
    raw = os.urandom(32)  # 256-bit
    plain = raw.hex()     # mail linkinde kullanacağız
    token_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return plain, token_hash

def create_user_token(
    db: Session,
    user_id,
    token_type: str,          # "invite" | "reset"
    ttl_minutes: int = 60*48  # default: 48 saat
) -> Tuple[UserToken, str]:
    # Eski ve kullanılmamış aynı tip tokenları (opsiyonel) iptal edelim:
    db.query(UserToken).filter(
        UserToken.user_id == user_id,
        UserToken.type == token_type,
        UserToken.used_at.is_(None)
    ).delete(synchronize_session=False)

    plain, token_hash = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

    ut = UserToken(
        user_id=user_id,
        type=token_type,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(ut)
    db.commit()
    db.refresh(ut)
    return ut, plain

def verify_token(
    db: Session,
    token_plain: str,
    token_type: str
) -> UserToken | None:
    token_hash = hashlib.sha256(token_plain.encode("utf-8")).hexdigest()
    ut = db.query(UserToken).filter(
        UserToken.token_hash == token_hash,
        UserToken.type == token_type,
        UserToken.used_at.is_(None)
    ).first()
    if not ut:
        return None
    # Süre kontrolü
    if ut.expires_at <= datetime.now(timezone.utc):
        return None
    return ut

def consume_token(db: Session, token: UserToken) -> None:
    token.used_at = datetime.now(timezone.utc)
    db.commit()
