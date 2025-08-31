# app/routes/auth.py

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserOut
from app.models.app_user import AppUser
from app.crud.user import get_user_by_username, get_user_by_id
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.config import settings

# 🔁 refresh token CRUD yardımcıları
from app.crud.refresh_token import (
    mint_refresh_token,
    consume_and_rotate,
    revoke_token,
    revoke_all_for_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ----- Cookie yardımcıları -----
# app/routes/auth.py (yardımcı fonksiyonların yerine)

def _normalize_cookie_domain(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    try:
        return raw.strip().encode("idna").decode("ascii")
    except Exception:
        return None

def set_refresh_cookie(response: Response, token: str, max_age_seconds: int | None = None) -> None:
    default_days = int(getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
    max_age = int(max_age_seconds if max_age_seconds is not None else default_days * 24 * 3600)
    cookie_name = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
    cookie_secure = bool(getattr(settings, "REFRESH_COOKIE_SECURE", False))
    cookie_samesite = getattr(settings, "REFRESH_COOKIE_SAMESITE", "lax")
    raw_domain = getattr(settings, "REFRESH_COOKIE_DOMAIN", None)
    cookie_domain = _normalize_cookie_domain(raw_domain)

    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        domain=cookie_domain,
        max_age=max_age,
        path="/",
    )

def clear_refresh_cookie(response: Response) -> None:
    cookie_name = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
    raw_domain = getattr(settings, "REFRESH_COOKIE_DOMAIN", None)
    cookie_domain = _normalize_cookie_domain(raw_domain)
    response.delete_cookie(key=cookie_name, domain=cookie_domain, path="/")



# ----- LOGIN: access + refresh(cookie) -----
@router.post("/token", response_model=Token, summary="Login for access token (sets refresh cookie)")
def login_for_access_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = Form(False), 
    db: Session = Depends(get_db),
):
    """
    Kullanıcıyı doğrular, kısa ömürlü **access token** döner ve
    uzun ömürlü **refresh token**'ı HttpOnly cookie olarak set eder.
    """
    user = get_user_by_username(db, form_data.username)
    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active" or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Access token (kısa ömür)
    access_token_expires = timedelta(minutes=int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    # Refresh (uzun ömür): remember=true ise settings gün sayısı, değilse daha kısa (ör. 1 gün)
    ua = request.headers.get("User-Agent")
    ip = request.client.host if request.client else None
    refresh_days = int(getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30)) if remember_me else 1
    plain_refresh, _ = mint_refresh_token(db, user.id, ua, ip, ttl_days=refresh_days)

    # Cookie ömrünü saniye olarak geçir
    set_refresh_cookie(response, plain_refresh, max_age_seconds=refresh_days * 24 * 3600)

    return {"access_token": access_token, "token_type": "bearer"}


# ----- REFRESH: access yenile + refresh rotasyon -----
@router.post("/refresh", response_model=Token, summary="Refresh access token (rotates refresh cookie)")
def refresh_access_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    HttpOnly cookie'deki refresh token doğrulanır, **rotasyon** yapılır,
    yeni access token ve yeni refresh cookie döner.
    """
    cookie_name = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
    plain = request.cookies.get(cookie_name)
    if not plain:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        user, new_plain, lifetime_seconds = consume_and_rotate(
            db,
            plain,
            user_agent=request.headers.get("User-Agent"),
            ip=request.client.host if request.client else None,
        )
    except ValueError:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    minutes = int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    access_token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(minutes=minutes))
    # Rotasyondan gelen orijinal kalan ömürle cookie max-age set edelim:
    set_refresh_cookie(response, new_plain, max_age_seconds=lifetime_seconds)
    return {"access_token": access_token, "token_type": "bearer"}


# ----- LOGOUT: tek cihaz -----
@router.post("/logout", summary="Logout from current device (revokes this refresh)")
def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    cookie_name = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
    plain = request.cookies.get(cookie_name)
    if plain:
        revoke_token(db, plain)
    clear_refresh_cookie(response)
    return {"ok": True}


# ----- LOGOUT-ALL: tüm cihazlar -----
@router.post("/logout-all", summary="Logout from all devices (revokes all refresh tokens)")
def logout_all(
    response: Response,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = revoke_all_for_user(db, current_user.id)
    clear_refresh_cookie(response)
    return {"revoked": count}


# ----- Kimliği doğrulanmış kullanıcı -----
@router.get("/me", response_model=UserOut, summary="Get current authenticated user")
def read_users_me(
    current_user: AppUser = Depends(get_current_user),
):
    """Mevcut oturumun kullanıcısını döner."""
    return current_user
