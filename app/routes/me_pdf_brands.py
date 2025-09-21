# app/routes/me_pdf_brand.py
from typing import Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser
from app.schemas.pdf import PdfBrandUpdate, PdfBrandOut, PdfBrandLogoOut
from app.crud import pdf as crud
from app.core.config import MEDIA_ROOT
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/me/pdf/brand", tags=["me-pdf-brand"])

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

def _content_type_from_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


# --------- Tekil Brand (me) ---------

@router.get("", response_model=PdfBrandOut)
def get_my_brand(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    """
    Kullanıcı için tek brand nesnesini döner. Yoksa varsayılanı oluşturur.
    """
    obj = crud.brand_ensure_default(db, current_user.id)
    return obj

@router.put("", response_model=PdfBrandOut)
def update_my_brand(payload: PdfBrandUpdate, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_ensure_default(db, current_user.id)
    return crud.brand_update(db, obj, key=payload.key, config_json=payload.config_json)

@router.delete("", status_code=204)
def delete_my_brand(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get_single(db, current_user.id)
    if not obj:
        return
    # Hard delete
    crud.brand_delete(db, obj)
    return


# --------- Brand Image (me) ---------

@router.get("/image", response_model=PdfBrandLogoOut)
def get_my_brand_logo(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get_single(db, current_user.id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    return {"brand_id": obj.id, "logo_url": obj.logo_url}

@router.post("/image", response_model=PdfBrandLogoOut, status_code=201)
def create_my_brand_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_ensure_default(db, current_user.id)
    if obj.logo_url:
        raise HTTPException(status_code=409, detail="Bu brand için logo zaten var. PUT ile güncelleyebilirsiniz.")
    ext = _pick_ext(file)
    dest = _brand_dir(obj.id) / f"logo{ext}"
    _save_upload(file, dest)
    url = _static_url(dest)
    obj = crud.brand_set_logo(db, obj, url)
    return {"brand_id": obj.id, "logo_url": obj.logo_url}

@router.put("/image", response_model=PdfBrandLogoOut)
def update_my_brand_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_ensure_default(db, current_user.id)

    old_path: Optional[Path] = None
    if obj.logo_url:
        rel = obj.logo_url.replace("/static/", "")
        old_path = Path(MEDIA_ROOT) / Path(rel)

    ext = _pick_ext(file)
    dest = _brand_dir(obj.id) / f"logo{ext}"
    _save_upload(file, dest)

    if old_path and old_path.resolve() != dest.resolve():
        _remove_file_safely(old_path)

    url = _static_url(dest)
    obj = crud.brand_set_logo(db, obj, url)
    return {"brand_id": obj.id, "logo_url": obj.logo_url}

@router.delete("/image", status_code=204)
def delete_my_brand_logo(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.brand_get_single(db, current_user.id)
    if not obj:
        return
    if obj.logo_url:
        rel = obj.logo_url.replace("/static/", "")
        fpath = Path(MEDIA_ROOT) / Path(rel)
        _remove_file_safely(fpath)
    crud.brand_clear_logo(db, obj)
    return

@router.get("/image/file")
def get_my_brand_logo_file(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    """
    Brand logosunu dosya (binary) olarak döndürür.
    """
    obj = crud.brand_get_single(db, current_user.id)
    if not obj:
        raise HTTPException(status_code=404, detail="Brand bulunamadı")
    if not obj.logo_url:
        raise HTTPException(status_code=404, detail="Bu brand için logo yok")

    rel = obj.logo_url.replace("/static/", "")
    fpath = Path(MEDIA_ROOT) / Path(rel)

    if not fpath.exists():
        folder = _brand_dir(obj.id)
        candidates = [p for p in folder.glob("logo.*") if p.suffix.lower() in ALLOWED_CONTENT_TYPES.values()]
        if not candidates:
            raise HTTPException(status_code=404, detail="Logo dosyası bulunamadı")
        fpath = candidates[0]

    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Logo dosyası bulunamadı")

    return FileResponse(
        path=fpath,
        media_type=_content_type_from_path(fpath),
    )
