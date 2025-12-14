from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.user import get_user_by_email, get_user_by_username
from app.models.app_user import AppUser
from app.services.tokens import verify_token, consume_token, create_user_token
from app.core.security import get_password_hash, verify_password
from app.core.mailer import send_email, brand_subject
from app.core.settings import settings
from app.api.deps import get_current_dealer  # ya da get_current_user
from app.schemas.user import (
    AcceptInviteIn,
    ForgotPasswordIn,
    ResetPasswordIn,
    ChangePasswordIn,
    ChangeUsernameIn,
    ChangeUsernameOut,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/accept-invite", status_code=200)
def accept_invite(payload: AcceptInviteIn, db: Session = Depends(get_db)):
    ut = verify_token(db, payload.token, token_type="invite")
    if not ut:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Geçersiz veya süresi dolmuş davet")
    user: AppUser = db.query(AppUser).filter(AppUser.id == ut.user_id, AppUser.is_deleted == False).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")

    # username benzersiz mi?
    if get_user_by_username(db, payload.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Kullanıcı adı kullanımda")

    user.username = payload.username
    user.password_hash = get_password_hash(payload.password)
    user.password_set_at = datetime.now(timezone.utc)
    user.status = "active"

    db.commit()
    consume_token(db, ut)
    return {"message": "Hesap etkinleştirildi. Giriş yapabilirsiniz."}

@router.post("/forgot-password", status_code=200)
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    user: AppUser = get_user_by_email(db, payload.email)
    # Güvenlik için: kullanıcı yoksa bile 200 döneriz (user-enumeration engeli)
    if user and not user.is_deleted:
        ut, plain = create_user_token(db, user_id=user.id, token_type="reset", ttl_minutes=60)  # 60 dk geçerli
        link = f"{settings.FRONTEND_URL}/reset-password?token={plain}"
        html = f"""
            <h3>{settings.BRAND_NAME} - Şifre Sıfırlama</h3>
            <p>Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın. 60 dakika geçerlidir:</p>
            <p><a href="{link}">{link}</a></p>
        """
        try:
            send_email(user.email, brand_subject("Şifre Sıfırlama"), html)
        except Exception:
            # e-posta hatasını kullanıcıya çaktırmayın
            pass
    return {"message": "Eğer e-posta kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."}

@router.post("/reset-password", status_code=200)
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    ut = verify_token(db, payload.token, token_type="reset")
    if not ut:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Geçersiz veya süresi dolmuş token")
    user: AppUser = db.query(AppUser).filter(AppUser.id == ut.user_id, AppUser.is_deleted == False).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")

    user.password_hash = get_password_hash(payload.password)
    user.password_set_at = datetime.now(timezone.utc)
    if user.status == "invited":
        user.status = "active"

    db.commit()
    consume_token(db, ut)
    return {"message": "Şifre güncellendi. Giriş yapabilirsiniz."}

@router.post("/change-password", status_code=200)
def change_password(payload: ChangePasswordIn, current=Depends(get_current_dealer), db: Session = Depends(get_db)):
    # Eski şifre doğru mu?
    if not current.password_hash or not verify_password(payload.old_password, current.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Eski şifre hatalı")

    # Yeni şifre hashle ve güncelle
    current.password_hash = get_password_hash(payload.new_password)
    current.password_set_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Şifre güncellendi"}

@router.post("/change-username", response_model=ChangeUsernameOut, status_code=200)
def change_username(payload: ChangeUsernameIn, current=Depends(get_current_dealer), db: Session = Depends(get_db)):
    if current.username == payload.username:
        return ChangeUsernameOut(username=current.username)

    existing = get_user_by_username(db, payload.username)
    if existing and existing.id != current.id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Bu kullanıcı adı kullanımda")

    current.username = payload.username
    db.commit()
    db.refresh(current)
    return ChangeUsernameOut(username=current.username)
