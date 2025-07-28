# app/routes/system_variant.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import os, shutil
from fastapi.responses import FileResponse
from pathlib import Path

from app.db.session import get_db
from app.crud.system_variant import (
    create_system_variant,
    get_system_variants,
    get_system_variant,
    update_system_variant,
    delete_system_variant,
    get_variants_for_system,
)

from app.crud.system import create_system_variant_with_templates, get_system_variant_detail

from app.schemas.system import (
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemVariantOut,
    SystemVariantCreateWithTemplates,
    SystemVariantDetailOut
)

router = APIRouter(prefix="/api/system-variants", tags=["SystemVariants"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VARIANT_PHOTO_DIR = os.path.join(BASE_DIR, "variant_photos")

@router.post("/system/{system_id}", response_model=SystemVariantOut, status_code=201)
def create_variant(
    system_id: UUID,
    payload: SystemVariantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new SystemVariant for a given System.
    """
    return create_system_variant(db, system_id, payload)

@router.get("/", response_model=list[SystemVariantOut])
def list_variants(db: Session = Depends(get_db)):
    """
    List all SystemVariants.
    """
    return get_system_variants(db)

#@router.get("/{variant_id}", response_model=SystemVariantOut)
#def get_variant_endpoint(
#    variant_id: UUID,
#    db: Session = Depends(get_db)
#):
#    """
#    Retrieve a specific SystemVariant by ID.
#    """
#    obj = get_system_variant(db, variant_id)
#    if not obj:
#        raise HTTPException(status_code=404, detail="SystemVariant not found")
#    return obj

@router.put("/{variant_id}", response_model=SystemVariantOut)
def update_variant(
    variant_id: UUID,
    payload: SystemVariantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update fields of an existing SystemVariant.
    """
    obj = update_system_variant(db, variant_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return obj

@router.delete("/{variant_id}", status_code=204)
def delete_variant(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a SystemVariant by ID.
    """
    deleted = delete_system_variant(db, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return

# ----- New: Variants by System -----
@router.get(
    "/system/{system_id}",
    response_model=list[SystemVariantOut],
    summary="List all SystemVariants for a given System ID"
)
def list_variants_by_system(
    system_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all variants for the specified system.
    """
    variants = get_variants_for_system(db, system_id)
    return variants

@router.post("/{variant_id}/photo", summary="Variant fotoğrafı yükle/güncelle")
def upload_or_replace_variant_photo(
    variant_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    obj = get_system_variant(db, variant_id)
    if not obj:
        raise HTTPException(404, "Variant not found")

    # Eski fotoğraf varsa sil
    if obj.photo_url:
        old_path = os.path.join(BASE_DIR, obj.photo_url)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Yeni fotoğrafı yükle
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{variant_id}{ext}"
    full_path = os.path.join(VARIANT_PHOTO_DIR, filename)

    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_url = f"variant_photos/{filename}"
    update_system_variant(db, variant_id, SystemVariantUpdate(photo_url=photo_url))

    return {
        "message": "Fotoğraf yüklendi/güncellendi",
        "photo_url": photo_url
    }

@router.delete("/{variant_id}/photo", summary="Variant fotoğrafını sil")
def delete_variant_photo(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    photo_path = os.path.join(BASE_DIR, obj.photo_url)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    update_system_variant(db, variant_id, SystemVariantUpdate(photo_url=None))

    return {"message": "Fotoğraf silindi"}

@router.get("/{variant_id}/photo", summary="Variant'a ait fotoğrafı döner")
def get_variant_photo_file(variant_id: UUID, db: Session = Depends(get_db)):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Variant için fotoğraf bilgisi bulunamadı")

    # Klasör yolu: proje kökü / variant_photos /
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    VARIANT_PHOTO_DIR = BASE_DIR / "variant_photos"

    filename = Path(obj.photo_url).name
    photo_path = VARIANT_PHOTO_DIR / filename

    if not photo_path.exists():
        raise HTTPException(404, f"Fotoğraf dosyası bulunamadı: {photo_path}")

    return FileResponse(path=str(photo_path), media_type="image/jpeg")

@router.post("/", response_model=SystemVariantDetailOut, status_code=201)
def create_variant_with_templates_endpoint(
    payload: SystemVariantCreateWithTemplates,
    db: Session = Depends(get_db)
):
    """
    Yeni system variant oluşturur ve ilişkili profil, cam, malzeme şablonlarını ekler.
    """
    variant = create_system_variant_with_templates(db, payload)
    detail = get_system_variant_detail(db, variant.id)
    if not detail:
        raise HTTPException(status_code=500, detail="Variant oluşturuldu ama detail alınamadı")
    return detail