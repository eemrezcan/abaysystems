# app/crud/refresh_token.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID
import secrets, hashlib, math

from app.models.RefreshToken import RefreshToken
from app.models.app_user import AppUser
from app.core.config import settings

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def mint_refresh_token(
    db: Session,
    user_id: UUID,
    user_agent: str | None,
    ip: str | None,
    ttl_days: int | None = None,   # 👈 (önceki adımda eklemiştik)
) -> tuple[str, RefreshToken]:
    days = int(ttl_days if ttl_days is not None else getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
    plain = secrets.token_urlsafe(48)
    rt = RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(plain),
        user_agent=user_agent,
        ip_address=ip,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=days),
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return plain, rt

def _get_valid_token(db: Session, plain: str) -> RefreshToken | None:
    now = datetime.utcnow()
    h = _hash_token(plain)
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == h,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .first()
    )

def consume_and_rotate(
    db: Session,
    plain: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[AppUser, str, int]:
    """
    Refresh token'ı doğrular, revoke eder ve aynı 'ömür' ile yenisini üretir.
    DÖNÜŞ: (user, new_plain_refresh, original_lifetime_seconds)
    """
    token = _get_valid_token(db, plain)
    if not token:
        raise ValueError("Invalid refresh token")

    user = db.query(AppUser).filter(AppUser.id == token.user_id).first()
    if not user:
        raise ValueError("User not found")

    # Orijinal ömrü saniye cinsinden hesapla (created_at → expires_at)
    lifetime_seconds = int((token.expires_at - token.created_at).total_seconds())
    lifetime_seconds = max(lifetime_seconds, 60)  # güvenlik için min 1 dk

    # Mevcut token'ı revoke et
    token.revoked_at = datetime.utcnow()
    db.add(token)
    db.flush()

    # Aynı ömürle yeni token üret (gün cinsine yuvarla)
    ttl_days = max(1, math.ceil(lifetime_seconds / 86400))
    new_plain, new_rt = mint_refresh_token(db, user.id, user_agent, ip, ttl_days=ttl_days)
    token.replaced_by = new_rt.id
    db.commit()

    return user, new_plain, lifetime_seconds

def revoke_token(db: Session, plain: str) -> bool:
    token = _get_valid_token(db, plain)
    if not token:
        return False
    token.revoked_at = datetime.utcnow()
    db.add(token)
    db.commit()
    return True

def revoke_all_for_user(db: Session, user_id: UUID) -> int:
    now = datetime.utcnow()
    q = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    tokens = q.all()
    for t in tokens:
        t.revoked_at = now
        db.add(t)
    db.commit()
    return len(tokens)
