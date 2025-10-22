# app/routes/me_profile_picture.py
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import MEDIA_ROOT
from app.core.security import get_current_user
from app.models.app_user import AppUser
from fastapi.responses import FileResponse
import mimetypes

from app.schemas.dealer_profile_picture import DealerProfilePictureOut
from app.crud import dealer_profile_picture as crud_dpp

router = APIRouter(prefix="/api/me", tags=["me-profile-picture"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png":  ".png",
    "image/webp": ".webp",
}

def _user_dir(user_id) -> Path:
    return Path(MEDIA_ROOT) / "dealers" / str(user_id)

def _save_upload(upload: UploadFile, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

def _remove_file_safely(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass

def _static_url_for(path: Path) -> str:
    rel = path.relative_to(MEDIA_ROOT).as_posix()
    return f"/static/{rel}"

def _pick_extension(upload: UploadFile) -> str:
    if upload.content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[upload.content_type]
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix in {".jpg", ".jpeg"}: return ".jpg"
    if suffix in {".png"}:          return ".png"
    if suffix in {".webp"}:         return ".webp"
    raise HTTPException(status_code=415, detail="Desteklenmeyen dosya türü. JPEG/PNG/WebP yükleyin.")

#@router.get("/profile-picture", response_model=DealerProfilePictureOut)
#def get_my_profile_picture(
#    db: Session = Depends(get_db),
#    current_user: AppUser = Depends(get_current_user),
#):
#    pic = crud_dpp.get_by_user_id(db, current_user.id)
#    if not pic:
#        raise HTTPException(status_code=404, detail="Profil fotoğrafı bulunamadı.")
#    return pic

@router.get("/profile-picture", response_class=FileResponse, summary="Profil fotoğrafını doğrudan resim olarak döndür")
def get_my_profile_picture_file(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Profil fotoğrafını dosya olarak döndürür.
    Kayıt yoksa veya dosya bulunamazsa 404 verir.
    """
    pic = crud_dpp.get_by_user_id(db, current_user.id)
    if not pic or not pic.image_url:
        raise HTTPException(status_code=404, detail="Profil fotoğrafı bulunamadı.")

    rel = pic.image_url.replace("/static/", "")
    fpath = Path(MEDIA_ROOT) / Path(rel)
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Profil fotoğrafı bulunamadı.")

    mime, _ = mimetypes.guess_type(str(fpath))
    if mime is None:
        mime = "image/jpeg"  # uzantıdan bulunamazsa varsayılan

    return FileResponse(
        path=str(fpath),
        media_type=mime,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.post("/profile-picture", response_model=DealerProfilePictureOut, status_code=201)
def create_my_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    exists = crud_dpp.get_by_user_id(db, current_user.id)
    if exists:
        raise HTTPException(status_code=409, detail="Zaten bir profil fotoğrafınız var. Lütfen PUT kullanın.")

    ext = _pick_extension(file)
    dest = _user_dir(current_user.id) / f"profile{ext}"

    _save_upload(file, dest)
    image_url = _static_url_for(dest)
    created = crud_dpp.create(db, current_user.id, image_url)
    return created

@router.put("/profile-picture", response_model=DealerProfilePictureOut)
def upsert_my_profile_picture(
    file: UploadFile = File(...),
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Upsert mantığı:
    - Kayıt YOKSA: dosyayı kaydeder, yeni kayıt oluşturur -> 201
    - Kayıt VARSA: dosyayı değiştirir, eski dosyayı (varsa) siler -> 200
    """
    pic = crud_dpp.get_by_user_id(db, current_user.id)

    # Varsa eski dosya yolunu not et
    old_path: Optional[Path] = None
    if pic and pic.image_url:
        rel = pic.image_url.replace("/static/", "")
        old_path = Path(MEDIA_ROOT) / Path(rel)

    # Yeni hedef yolu hazırla
    ext = _pick_extension(file)
    dest = _user_dir(current_user.id) / f"profile{ext}"

    # Dosyayı yaz
    _save_upload(file, dest)

    # Eski dosya farklı uzantıda ise temizle
    if old_path and old_path.resolve() != dest.resolve():
        _remove_file_safely(old_path)

    image_url = _static_url_for(dest)

    if not pic:
        created = crud_dpp.create(db, current_user.id, image_url)
        if response is not None:
            response.status_code = status.HTTP_201_CREATED
        return created
    else:
        updated = crud_dpp.update_url(db, pic, image_url)
        # 200 varsayılan
        return updated


@router.delete("/profile-picture", status_code=204)
def delete_my_profile_picture(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pic = crud_dpp.get_by_user_id(db, current_user.id)
    if not pic:
        return
    if pic.image_url:
        rel = pic.image_url.replace("/static/", "")
        fpath = Path(MEDIA_ROOT) / Path(rel)
        _remove_file_safely(fpath)
    crud_dpp.delete(db, pic)
    return
