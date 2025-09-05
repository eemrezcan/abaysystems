# app/routes/me_pdf_brands.py
from typing import List, Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser
from app.schemas.pdf import PdfBrandCreate, PdfBrandUpdate, PdfBrandOut, PdfBrandLogoOut
from app.crud import pdf as crud
from app.core.config import MEDIA_ROOT

router = APIRouter(prefix="/api/me/pdf/brands", tags=["me-pdf-brands"])

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

def _brand_dir(brand_id: UUID) -> Path:
    return Path(MEDIA_ROOT) / "brands" / str(brand_id)

def _pick_ext(upload: UploadFile) -> str:
    if upload.content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[upload.content_type]
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix in {".jpg", ".jpeg"}: return ".jpg"
    if suffix == ".png": return ".png"
    if suffix == ".webp": return ".webp"
    raise HTTPException(status_code=415, detail="JPEG/PNG/WebP yükleyin.")

def _save_upload(upload: UploadFile, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

def _static_url(path: Path) -> str:
    rel = path.relative_to(MEDIA_ROOT).as_posix()
    return f"/static/{rel}"

def _remove_file_safely(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass
# --------- Brands CRUD (me) ---------

@router.get("", response_model=List[PdfBrandOut])
def list_my_brands(q: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    return crud.brands_list(db, owner_id=current_user.id, q=q)

@router.get("/{id}", response_model=PdfBrandOut)
def get_my_brand(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    return obj

@router.get("/by-key/{key}", response_model=PdfBrandOut)
def get_my_brand_by_key(key: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get_by_key(db, current_user.id, key)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    return obj

@router.post("", response_model=PdfBrandOut, status_code=201)
def create_my_brand(payload: PdfBrandCreate, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    if crud.brand_get_by_key(db, current_user.id, payload.key):
        raise HTTPException(status_code=409, detail="Bu key ile brand zaten var")
    return crud.brand_create(db, owner_id=current_user.id, key=payload.key, config_json=payload.config_json)

@router.put("/{id}", response_model=PdfBrandOut)
def update_my_brand(id: UUID, payload: PdfBrandUpdate, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    if payload.key and payload.key != obj.key:
        if crud.brand_get_by_key(db, current_user.id, payload.key):
            raise HTTPException(status_code=409, detail="Bu key ile başka brand var")
    return crud.brand_update(db, obj, key=payload.key, config_json=payload.config_json)

@router.delete("/{id}", status_code=204)
def delete_my_brand(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        return
    crud.brand_soft_delete(db, obj)
    return

# --------- Brand Image (me) ---------

@router.get("/{id}/image", response_model=PdfBrandLogoOut)
def get_my_brand_logo(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    return {"brand_id": id, "logo_url": obj.logo_url}

@router.post("/{id}/image", response_model=PdfBrandLogoOut, status_code=201)
def create_my_brand_logo(id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    if obj.logo_url:
        raise HTTPException(status_code=409, detail="Bu brand için logo zaten var. PUT ile güncelleyebilirsiniz.")
    ext = _pick_ext(file)
    dest = _brand_dir(id) / f"logo{ext}"
    _save_upload(file, dest)
    url = _static_url(dest)
    obj = crud.brand_set_logo(db, obj, url)
    return {"brand_id": id, "logo_url": obj.logo_url}

@router.put("/{id}/image", response_model=PdfBrandLogoOut)
def update_my_brand_logo(id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")

    # Eski dosya yolu (varsa)
    old_path: Optional[Path] = None
    if obj.logo_url:
        rel = obj.logo_url.replace("/static/", "")
        old_path = Path(MEDIA_ROOT) / Path(rel)

    ext = _pick_ext(file)
    dest = _brand_dir(id) / f"logo{ext}"

    # Yeni dosyayı kaydet
    _save_upload(file, dest)

    # Eski dosya farklı bir path ise sil (örn. .png -> .webp)
    if old_path and old_path.resolve() != dest.resolve():
        _remove_file_safely(old_path)

    url = _static_url(dest)
    obj = crud.brand_set_logo(db, obj, url)
    return {"brand_id": id, "logo_url": obj.logo_url}

@router.delete("/{id}/image", status_code=204)
def delete_my_brand_logo(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get(db, current_user.id, id)
    if not obj:
        return

    # Dosyayı sil
    if obj.logo_url:
        rel = obj.logo_url.replace("/static/", "")
        fpath = Path(MEDIA_ROOT) / Path(rel)
        _remove_file_safely(fpath)

    # DB’de logo_url=None
    crud.brand_clear_logo(db, obj)
    return
