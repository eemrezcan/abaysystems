# app/routes/system_variant.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import os, shutil
from fastapi.responses import FileResponse
from pathlib import Path

from app.db.session import get_db

from math import ceil
from fastapi import Query  # varsa tekrar ekleme

# 🔐 rol kontrolü
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 filtreler için modeller
from app.models.system import System, SystemVariant

from app.schemas.system import SystemVariantUpdate, SystemVariantOut, SystemVariantPageOut

from app.crud.system_variant import (
    create_system_variant,
    get_system_variant,
    update_system_variant,
    delete_system_variant,
    get_variants_for_system,  # admin için kullanılabilir; bayi filtreleri için aşağıda ORM query kullanıyoruz
    get_system_variants_page,
    get_variants_for_system_page,

)

from app.crud.system import (
    create_system_variant_with_templates,
    get_system_variant_detail,
    update_system_variant_with_templates,

)

from app.schemas.system import (
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemVariantOut,
    SystemVariantCreateWithTemplates,
    SystemVariantDetailOut,
    SystemVariantUpdateWithTemplates,
)

router = APIRouter(prefix="/api/system-variants", tags=["SystemVariants"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VARIANT_PHOTO_DIR = os.path.join(BASE_DIR, "variant_photos")


# -----------------------------------------------------------------------------
# GET uçları: bayi + admin (bayi → sadece published & not-deleted)
# -----------------------------------------------------------------------------

@router.get("/", response_model=SystemVariantPageOut)
def list_variants(
    q: str | None = Query(None, description="Varyant veya sistem adına göre filtre"),
    # limit artık string; "all" desteklenir
    limit: str = Query("50", description='Sayfa başına kayıt. "all" desteklenir.'),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")

    # "all" → None (sınırsız), sayı → int (1..200 aralığına sıkıştır)
    limit_val = None if isinstance(limit, str) and limit.lower() == "all" else int(limit)
    if limit_val is not None:
        limit_val = max(1, min(limit_val, 200))
    offset = 0 if limit_val is None else (page - 1) * limit_val

    items, total = get_system_variants_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit_val,   # None ise CRUD'da LIMIT uygulanmamalı
        offset=offset,
    )

    if limit_val is None:
        # "all" modunda tek sayfa mantığı
        effective_limit = total
        total_pages = 1 if total > 0 else 0
        page_out = 1
        has_next = False
        has_prev = False
    else:
        effective_limit = limit_val
        total_pages = ceil(total / limit_val) if total > 0 else 0
        page_out = page
        has_next = (page < total_pages) if total_pages > 0 else False
        has_prev = (page > 1) and (total_pages > 0)

    return SystemVariantPageOut(
        items=items,
        total=total,
        page=page_out,
        limit=effective_limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )




@router.get(
    "/system/{system_id}",
    response_model=SystemVariantPageOut,
    summary="Belirli bir sistemin varyantlarını (sayfalı) listele"
)
def list_variants_by_system(
    system_id: UUID,
    q: str | None = Query(None, description="Varyant adına göre filtre"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_variants_for_system_page(
        db=db,
        system_id=system_id,
        is_admin=is_admin,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return SystemVariantPageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )



@router.get("/{variant_id}/photo", summary="Variant'a ait fotoğrafı döner")
def get_variant_photo_file(
    variant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Variant için fotoğraf bilgisi bulunamadı")

    # Bayi unpublished/silinmiş variant veya sistemi görmesin
    if current_user.role != "admin":
        # variant ve bağlı sistem publish/deleted kontrolü
        if obj.is_deleted or not obj.is_published:
            raise HTTPException(404, "Variant için fotoğraf bilgisi bulunamadı")
        sys = getattr(obj, "system", None)
        if not sys or sys.is_deleted or not sys.is_published:
            raise HTTPException(404, "Variant için fotoğraf bilgisi bulunamadı")

    # Klasör yolu: proje kökü / variant_photos /
    BASE_DIR_LOCAL = Path(__file__).resolve().parent.parent.parent
    VARIANT_PHOTO_DIR_LOCAL = BASE_DIR_LOCAL / "variant_photos"

    filename = Path(obj.photo_url).name
    photo_path = VARIANT_PHOTO_DIR_LOCAL / filename

    if not photo_path.exists():
        raise HTTPException(404, f"Fotoğraf dosyası bulunamadı: {photo_path}")

    return FileResponse(path=str(photo_path), media_type="image/jpeg")


# -----------------------------------------------------------------------------
# Mutasyon uçları: ADMIN-ONLY
# -----------------------------------------------------------------------------

@router.post("/system/{system_id}", response_model=SystemVariantOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_variant(
    system_id: UUID,
    payload: SystemVariantCreate,
    db: Session = Depends(get_db)
):
    """
    Verilen System için yeni SystemVariant oluşturur.
    """
    # klasör yoksa oluştur (foto yükleme için)
    if not os.path.exists(VARIANT_PHOTO_DIR):
        os.makedirs(VARIANT_PHOTO_DIR, exist_ok=True)
    return create_system_variant(db, system_id, payload)


@router.put("/{variant_id}", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def update_variant(
    variant_id: UUID,
    payload: SystemVariantUpdate,
    db: Session = Depends(get_db)
):
    """
    Mevcut SystemVariant alanlarını günceller.
    """
    obj = update_system_variant(db, variant_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return obj


@router.delete("/{variant_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_variant(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    SystemVariant siler (bizde soft delete alanı var; CRUD içinde buna göre davranır).
    """
    deleted = delete_system_variant(db, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return


@router.post("/{variant_id}/photo", summary="Variant fotoğrafı yükle/güncelle", dependencies=[Depends(get_current_admin)])
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

    # Klasör yoksa oluştur
    if not os.path.exists(VARIANT_PHOTO_DIR):
        os.makedirs(VARIANT_PHOTO_DIR, exist_ok=True)

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


@router.delete("/{variant_id}/photo", summary="Variant fotoğrafını sil", dependencies=[Depends(get_current_admin)])
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


@router.post("/", response_model=SystemVariantDetailOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_variant_with_templates_endpoint(
    payload: SystemVariantCreateWithTemplates,
    db: Session = Depends(get_db)
):
    """
    Yeni system variant oluşturur ve ilişkili profil, cam, malzeme şablonlarını ekler.
    """
    # klasör yoksa oluştur (foto yükleme için)
    if not os.path.exists(VARIANT_PHOTO_DIR):
        os.makedirs(VARIANT_PHOTO_DIR, exist_ok=True)

    variant = create_system_variant_with_templates(db, payload)
    detail = get_system_variant_detail(db, variant.id)
    if not detail:
        raise HTTPException(status_code=500, detail="Variant oluşturuldu ama detail alınamadı")
    return detail


@router.put(
    "/{variant_id}/templates",
    response_model=SystemVariantDetailOut,
    summary="Bir SystemVariant ve tüm profil/cam/malzeme şablonlarını güncelle",
    dependencies=[Depends(get_current_admin)]
)
def update_variant_templates_endpoint(
    variant_id: UUID,
    payload: SystemVariantUpdateWithTemplates,
    db: Session = Depends(get_db)
):
    """
    Mevcut bir variant’ın adını ve ilişkili tüm şablonlarını günceller.
    """
    try:
        variant = update_system_variant_with_templates(db, variant_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    detail = get_system_variant_detail(db, variant.id)
    if not detail:
        raise HTTPException(status_code=500, detail="Unable to fetch updated variant detail")
    return detail

@router.put("/{variant_id}/publish", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def publish_variant(
    variant_id: UUID,
    db: Session = Depends(get_db),
):
    v = get_system_variant(db, variant_id)
    if not v or v.is_deleted:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Ebeveyn sistemi güvenle bul
    parent = getattr(v, "system", None)
    if parent is None:
        parent = db.query(System).filter(System.id == v.system_id).first()

    if parent is None or getattr(parent, "is_deleted", False):
        raise HTTPException(status_code=400, detail="Parent system is deleted or missing")

    if not getattr(parent, "is_published", False):
        raise HTTPException(status_code=400, detail="Parent system must be published first")

    updated = update_system_variant(db, variant_id, SystemVariantUpdate(is_published=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated


@router.put("/{variant_id}/unpublish", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def unpublish_variant(
    variant_id: UUID,
    db: Session = Depends(get_db),
):
    v = get_system_variant(db, variant_id)
    if not v or v.is_deleted:
        raise HTTPException(status_code=404, detail="Variant not found")

    updated = update_system_variant(db, variant_id, SystemVariantUpdate(is_published=False))
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated
