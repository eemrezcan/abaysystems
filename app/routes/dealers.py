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
from app.core.mailer import send_email as send_mail_fn

from typing import List, Optional
from fastapi import Query
from sqlalchemy import or_, func
from app.services.tokens import create_user_token
from app.core.settings import settings
from app.core.mailer import send_email
from app.models.user_token import UserToken

from app.schemas.user import DealerOut, DealerReactivateIn

from math import ceil
from app.crud.user import get_dealers_page  # 🟢 eklendi
from app.schemas.user import DealerPageOut  # 🟢 eklendi
from datetime import datetime, timezone

router = APIRouter(prefix="/api/dealers", tags=["Dealers"])

@router.post("/invite", response_model=DealerOut, status_code=201, dependencies=[Depends(get_current_admin)])
def invite_dealer(payload: DealerInviteCreate, db: Session = Depends(get_db)):
    # 🔁 Eskiden: exists = get_user_by_email(db, payload.email)  (yalnızca is_deleted=False döndürüyordu)
    # 🟢 Yeni: e-postayı is_deleted *dahil* her durumda ham sorgu ile bul
    existing = db.query(AppUser).filter(AppUser.email == payload.email).first()

    # 🟢 1) Aktif/askıda kayıt varsa: yeniden davete gerek yok → 409
    if existing and not existing.is_deleted:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kayıtlı")

    # 🟢 2) Silinmiş kayıt varsa: restore + re-invite
    if existing and existing.is_deleted:
        existing.is_deleted = False
        existing.status = "invited"
        existing.username = None
        existing.password_hash = None
        existing.password_set_at = None

        # Profil bilgilerini güncelle (gelen payload'a göre)
        existing.name = payload.name
        existing.phone = payload.phone
        existing.owner_name = payload.owner_name
        existing.city = payload.city

        db.add(existing)
        db.commit()
        db.refresh(existing)

        # Eski "invite" tokenlarını iptal ederek yeni token üret
        ut, plain = create_user_token(db, user_id=existing.id, token_type="invite", ttl_minutes=60*48)

        link = f"{settings.FRONTEND_URL}/set-password?token={plain}"
        html = f"""
            <h3>Abay Systems - Bayi Daveti (Yeniden)</h3>
            <p>Merhaba {existing.name},</p>
            <p>Hesabınızı etkinleştirmek için aşağıdaki bağlantıya tıklayın ve kullanıcı adı/şifrenizi belirleyin:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Bağlantı 48 saat geçerlidir.</p>
        """
        try:
            send_email(existing.email, "Bayi Daveti - Abay Systems", html)
        except Exception as e:
            # Mail gönderimi başarısızsa kullanıcı geri döndürülebilir ama burada 500 veriyoruz
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

        # DEBUG modda token döndürmek testleri kolaylaştırır (resend-invite’ta yaptığımız gibi)
        if getattr(settings, "DEBUG", False):
            return {**DealerOut.from_orm(existing).dict(), "debug_token": plain}  # Pydantic v1 için

        return existing

    # 🟢 3) Hiç kayıt yoksa: yeni "invited" kullanıcı oluştur + davet
    user = AppUser(
        username=None,
        password_hash=None,
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

    ut, plain = create_user_token(db, user_id=user.id, token_type="invite", ttl_minutes=60*48)

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
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

    if getattr(settings, "DEBUG", False):
        return {**DealerOut.from_orm(user).dict(), "debug_token": plain}

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
@router.get("/", response_model=DealerPageOut, dependencies=[Depends(get_current_admin)])
def list_dealers(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="İsme/emaile/şehre göre filtre"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
):
    offset = (page - 1) * limit

    items, total = get_dealers_page(
        db=db,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return DealerPageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )

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

@router.post(
    "/reactivate",
    response_model=DealerOut,
    status_code=200,
    dependencies=[Depends(get_current_admin)]
)
def reactivate_dealer(
    payload: DealerReactivateIn,
    send_invite: bool = Query(False, description="True ise re-activate sonrası davet maili gönderir."),
    db: Session = Depends(get_db),
):
    # 1) Hedef kullanıcıyı sadece silinmişler arasından bul (id veya email)
    q = db.query(AppUser).filter(AppUser.is_deleted == True, AppUser.role == "dealer")

    target = None
    if payload.id:
        target = q.filter(AppUser.id == payload.id).first()
    elif payload.email:
        target = q.filter(func.lower(AppUser.email) == payload.email.lower()).order_by(AppUser.updated_at.desc()).first()

    if not target:
        # Silinmemiş (aktif) bir kullanıcı olma ihtimalini kontrol edip ona göre mesaj verelim
        active = None
        if payload.id:
            active = db.query(AppUser).filter(AppUser.id == payload.id, AppUser.role == "dealer", AppUser.is_deleted == False).first()
        elif payload.email:
            active = db.query(AppUser).filter(func.lower(AppUser.email) == payload.email.lower(), AppUser.role == "dealer", AppUser.is_deleted == False).first()
        if active:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Bayi zaten aktif (silinmiş değil).")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Silinmiş böyle bir bayi bulunamadı.")

    # 2) Reactivate
    target.is_deleted = False
    # Hesap kurulmuş mu? (parola set edilmişse aktif kabul edelim)
    if target.password_hash:
        target.status = "active"
    else:
        target.status = "invited"

    db.add(target)
    db.commit()
    db.refresh(target)

    # 3) (Opsiyonel) Daveti mail ile yeniden gönder
    if send_invite and target.status != "active":
        ut, plain = create_user_token(db, user_id=target.id, token_type="invite", ttl_minutes=60*48)
        link = f"{settings.FRONTEND_URL}/set-password?token={plain}"
        html = f"""
            <h3>Abay Systems - Bayi Yeniden Aktivasyon & Davet</h3>
            <p>Merhaba {target.name},</p>
            <p>Hesabınız yeniden etkinleştirildi. Kullanıcı adı/şifre belirlemek için:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Bağlantı 48 saat geçerlidir.</p>
        """
        try:
            send_email(target.email, "Bayi Daveti - Abay Systems", html)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

        # DEBUG modda token ham değerini tester için döndürelim
        if getattr(settings, "DEBUG", False):
            out = DealerOut.from_orm(target).dict()
            out["debug_token"] = plain
            return out

    return target

@router.get("/{dealer_id}/invite-token", dependencies=[Depends(get_current_admin)])
def get_dealer_invite_token(dealer_id: UUID, db: Session = Depends(get_db)):
    """
    Bir bayinin mevcut 'invite' token durumunu döndürür.
    - Varsa: token meta bilgileri (plain token geri kazanılamaz)
    - Yoksa: 'aktif token yok umutcan yazssın.' mesajı
    """
    user = db.query(AppUser).filter(
        AppUser.id == dealer_id,
        AppUser.role == "dealer",
        AppUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")

    now = datetime.now(timezone.utc)

    ut = db.query(UserToken).filter(
        UserToken.user_id == user.id,
        UserToken.type == "invite",
        UserToken.used_at.is_(None),
        (UserToken.expires_at.is_(None)) | (UserToken.expires_at > now)
    ).order_by(UserToken.created_at.desc()).first()

    if not ut:
        # İstenen çıktı metni
        return {"message": "aktif token yok umutcan yazssın."}

    # Not: Güvenlik gereği 'plain' token geri kazanılamaz (hash saklıyoruz).
    # DEBUG ortamında bile plain üretilmemişse gösteremeyiz.
    return {
        "dealer_id": str(dealer_id),
        "invite_token": {
            "id": str(ut.id),
            "created_at": ut.created_at,
            "expires_at": ut.expires_at,
            "is_active": True
        },
        "note": "Mevcut token plain değeri güvenlik nedeniyle saklanmaz. Kullanılabilir link istiyorsanız /api/dealers/{dealer_id}/resend-invite çağırın."
    }

@router.post("/{dealer_id}/invite-link", status_code=200, dependencies=[Depends(get_current_admin)])
def issue_invite_link(
    dealer_id: UUID,
    send_email: bool = Query(False, description="True ise link mail olarak da gönderilir"),
    db: Session = Depends(get_db),
):
    """
    Bayi için yeni bir invite token üretir, önceki 'invite' tokenlarını iptal eder
    ve mailde gönderilenle aynı linki response olarak döner.
    Admin-only.
    """
    user = db.query(AppUser).filter(
        AppUser.id == dealer_id,
        AppUser.role == "dealer",
        AppUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bayi bulunamadı")

    if user.status == "active":
        # İstersek aktif kullanıcıya da link üretebiliriz, ama genelde gerekmez:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Kullanıcı zaten aktif")

    # Eski invite tokenlarını iptal et (kullanılmamış olanları)
    db.query(UserToken).filter(
        UserToken.user_id == user.id,
        UserToken.type == "invite",
        UserToken.used_at.is_(None)
    ).delete(synchronize_session=False)
    db.commit()

    # Yeni token üret
    ut, plain = create_user_token(
        db,
        user_id=user.id,
        token_type="invite",
        ttl_minutes=60 * 48
    )

    invite_link = f"{settings.FRONTEND_URL}/set-password?token={plain}"

    # İsteğe bağlı: e-posta gönder
    if send_email:
        html = f"""
            <h3>Abay Systems - Bayi Daveti</h3>
            <p>Merhaba {user.name},</p>
            <p>Hesabınızı etkinleştirmek için aşağıdaki bağlantıya tıklayın ve kullanıcı adı/şifrenizi belirleyin:</p>
            <p><a href="{invite_link}">{invite_link}</a></p>
            <p>Bağlantı 48 saat geçerlidir.</p>
        """
        try:
            send_mail_fn(user.email, "Bayi Daveti - Abay Systems", html)
        except Exception as e:
            # Mail başarısız olsa bile link response'ta dönüyor olacağız
            # İstersen 200 yerine 500 dönmeyi de tercih edebilirsin.
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Davet maili gönderilemedi: {e}")

    return {
        "dealer_id": str(user.id),
        "invite_link": invite_link,          # ← maildeki link birebir
        "expires_at": ut.expires_at,
        "email_sent": send_email
    }