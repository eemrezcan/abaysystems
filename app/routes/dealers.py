# app/routes/dealers.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_admin
from app.models.app_user import AppUser
from app.schemas.user import DealerInviteCreate, DealerUpdate, DealerOut
from app.crud.user import get_user_by_email, get_user_by_username
from app.core.mailer import send_email
from app.core.settings import settings
from app.services.tokens import create_user_token

from typing import List, Optional
from fastapi import Query
from sqlalchemy import or_
from app.services.tokens import create_user_token
from app.core.settings import settings
from app.core.mailer import send_email
from app.models.user_token import UserToken

router = APIRouter(prefix="/api/dealers", tags=["Dealers"])

@router.post("/invite", response_model=DealerOut, status_code=201, dependencies=[Depends(get_current_admin)])
def invite_dealer(payload: DealerInviteCreate, db: Session = Depends(get_db)):
    # Email benzersizliği
    exists = get_user_by_email(db, payload.email)
    if exists and not exists.is_deleted:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kayıtlı")
    if exists and exists.is_deleted:
        # İsterseniz burada 'geri getir' mantığı yazılabilir; şimdilik 409 verelim
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Bu e-posta eski bir kullanıcıya ait (silinmiş)")

    # Kullanıcıyı 'invited' olarak oluştur
    user = AppUser(
        username=None,                 # aktivasyonda set edilecek
        password_hash=None,            # aktivasyonda set edilecek
        role="dealer",
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        owner_name=payload.owner_name,
        city=payload.city,
        status="invited",
        is_deleted=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Davet tokeni üret
    ut, plain = create_user_token(db, user_id=user.id, token_type="invite", ttl_minutes=60*48)

    # Davet maili
    link = f"{settings.FRONTEND_URL}/set-password?token={plain}"
    html = f"""
        <h3>Abay Systems - Bayi Daveti</h3>
        <p>Merhaba {user.name},</p>
        <p>Hesabınızı etkinleştirmek için aşağıdaki bağlantıya tıklayın ve kullanıcı adı ile şifrenizi belirleyin:</p>
        <p><a href="{link}">{link}</a></p>
        <p>Bağlantı 48 saat içinde geçerlidir.</p>
    """
    try:
        send_email(user.email, "Bayi Daveti - Abay Systems", html)
    except Exception as e:
        # Mail hata verse de kullanıcı oluşturuldu; isterseniz burada rollback tercih edebilirsiniz.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

    return user

@router.put("/{dealer_id}", response_model=DealerOut, dependencies=[Depends(get_current_admin)])
def update_dealer(dealer_id: UUID, payload: DealerUpdate, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.id == dealer_id, AppUser.role == "dealer", AppUser.is_deleted == False).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")

    # Email değiştirilirse benzersizlik
    if payload.email and payload.email != user.email:
        if get_user_by_email(db, payload.email):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kullanımda")

    for field in ("name","email","phone","owner_name","city","status"):
        val = getattr(payload, field)
        if val is not None:
            setattr(user, field, val)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{dealer_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_dealer(dealer_id: UUID, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.id == dealer_id, AppUser.role == "dealer", AppUser.is_deleted == False).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")

    # Soft delete
    user.is_deleted = True
    db.commit()
    return

# 3.1 — Bayileri listele (admin-only)
@router.get("/", response_model=List[DealerOut], dependencies=[Depends(get_current_admin)])
def list_dealers(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="İsme/emaile göre filtre"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(AppUser).filter(AppUser.role == "dealer", AppUser.is_deleted == False)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(AppUser.name.ilike(like), AppUser.email.ilike(like), AppUser.city.ilike(like)))
    return query.order_by(AppUser.created_at.desc()).limit(limit).offset(offset).all()

# 3.2 — Daveti tekrar gönder (eski invite tokenlarını geçersiz kılar)
@router.post("/{dealer_id}/resend-invite", status_code=200, dependencies=[Depends(get_current_admin)])
def resend_invite(dealer_id: UUID, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(
        AppUser.id == dealer_id,
        AppUser.role == "dealer",
        AppUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")

    if user.status == "active":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Kullanıcı zaten aktif")

    # Önceki invite token'larını iptal et
    db.query(UserToken).filter(
        UserToken.user_id == user.id,
        UserToken.type == "invite",
        UserToken.used_at.is_(None)
    ).delete(synchronize_session=False)
    db.commit()

    # Yeni token üret ve mail gönder
    ut, plain = create_user_token(db, user_id=user.id, token_type="invite", ttl_minutes=60*48)
    link = f"{settings.FRONTEND_URL}/set-password?token={plain}"
    html = f"""
        <h3>Abay Systems - Bayi Daveti (Yeniden)</h3>
        <p>Merhaba {user.name},</p>
        <p>Hesabınızı etkinleştirmek için bağlantı:</p>
        <p><a href="{link}">{link}</a></p>
        <p>48 saat içinde geçerlidir.</p>
    """
    try:
        send_email(user.email, "Bayi Daveti (Yeniden) - Abay Systems", html)
    except Exception as e:
        # Mail hatası durumunda 500 dön
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

    # DEBUG modda token'ı geri döndürelim (yalnızca yerelde pratik test için)
    if settings.DEBUG:
        return {"message": "Davet yeniden gönderildi", "debug_token": plain}
    return {"message": "Davet yeniden gönderildi"}

# 3.3 — Askıya al / yeniden aktifleştir (login engellemek için)
@router.post("/{dealer_id}/suspend", status_code=200, dependencies=[Depends(get_current_admin)])
def suspend_dealer(dealer_id: UUID, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(
        AppUser.id == dealer_id, AppUser.role == "dealer", AppUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")
    user.status = "suspended"
    db.commit()
    return {"message": "Bayi askıya alındı"}

@router.post("/{dealer_id}/activate", status_code=200, dependencies=[Depends(get_current_admin)])
def activate_dealer(dealer_id: UUID, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(
        AppUser.id == dealer_id, AppUser.role == "dealer", AppUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")
    user.status = "active"
    db.commit()
    return {"message": "Bayi yeniden aktifleştirildi"}