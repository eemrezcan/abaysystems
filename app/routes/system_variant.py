# app/routes/system_variant.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from uuid import UUID
import os, shutil
from fastapi.responses import FileResponse
from pathlib import Path
from math import ceil
from sqlalchemy import asc, desc

from app.db.session import get_db

# 🔐 rol kontrolü
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 filtreler için modeller
from app.models.system import System, SystemVariant

from app.crud.system_variant import (
    create_system_variant,
    get_system_variant,
    update_system_variant,
    delete_system_variant,
    get_variants_for_system,        # (opsiyonel kullanım)
    get_system_variants_page,       # ✅ only_active desteği var
    get_variants_for_system_page,   # ✅ only_active desteği var
    reassign_variant_system,   # ✅ EKLE
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
    SystemVariantPageOut,
    SystemVariantReassignIn,   
    SystemVariantReorderIn, 
)

router = APIRouter(prefix="/api/system-variants", tags=["SystemVariants"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VARIANT_PHOTO_DIR = os.path.join(BASE_DIR, "variant_photos")


def _media_type_for_image(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".webp",):
        return "image/webp"
    return "image/jpeg"


# -----------------------------------------------------------------------------
# GET uçları: bayi + admin (bayi → sadece published & not-deleted)
# -----------------------------------------------------------------------------

@router.get("/", response_model=SystemVariantPageOut)
def list_variants(
    q: str | None = Query(None, description="Varyant veya sistem adına göre filtre"),
    # limit artık string; 'all' desteklenir
    limit: str = Query("50", description='Sayfa başına kayıt. "all" desteklenir.'),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    only_active: bool | None = Query(  # ✅ YENİ
        None,
        description="Sadece aktif varyantları getir. True/False/None (filtreleme yok)."
    ),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")

    # 'all' → None (sınırsız), sayı → int (1..200 aralığına sıkıştır)
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
        only_active=only_active,  # ✅
    )

    if limit_val is None:
        # 'all' modunda tek sayfa
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
    summary="Belirli bir sistemin varyantlarını (sayfalı) listele",
)
def list_variants_by_system(
    system_id: UUID,
    q: str | None = Query(None, description="Varyant adına göre filtre"),
    # limit artık string — 'all' kabul eder
    limit: str = Query("50", description='Sayfa başına kayıt. "all" desteklenir.'),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    only_active: bool | None = Query(  # ✅ YENİ
        None,
        description="Sadece aktif varyantları getir. True/False/None (filtreleme yok)."
    ),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")

    # 'all' → None (sınırsız); sayı → int ve 1..200 içine sıkıştır
    limit_val = None if isinstance(limit, str) and limit.lower() == "all" else int(limit)
    if limit_val is not None:
        limit_val = max(1, min(limit_val, 200))
    offset = 0 if limit_val is None else (page - 1) * limit_val

    items, total = get_variants_for_system_page(
        db=db,
        system_id=system_id,
        is_admin=is_admin,
        q=q,
        limit=limit_val,   # None gelirse CRUD tarafında LIMIT uygulanmamalı
        offset=offset,
        only_active=only_active,  # ✅
    )

    if limit_val is None:
        # 'all' modunda tek sayfa
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


@router.get("/{variant_id}/pdf-photo", summary="Variant'a ait PDF foto çıktısını döner")
def get_variant_pdf_photo_file(
    variant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.pdf_foto_cikti:
        raise HTTPException(404, "Variant için PDF foto bilgisi bulunamadı")

    if current_user.role != "admin":
        if obj.is_deleted or not obj.is_published:
            raise HTTPException(404, "Variant için PDF foto bilgisi bulunamadı")
        sys = getattr(obj, "system", None)
        if not sys or sys.is_deleted or not sys.is_published:
            raise HTTPException(404, "Variant için PDF foto bilgisi bulunamadı")

    BASE_DIR_LOCAL = Path(__file__).resolve().parent.parent.parent
    VARIANT_PHOTO_DIR_LOCAL = BASE_DIR_LOCAL / "variant_photos"

    filename = Path(obj.pdf_foto_cikti).name
    photo_path = VARIANT_PHOTO_DIR_LOCAL / filename

    if not photo_path.exists():
        raise HTTPException(404, f"PDF fotoğraf dosyası bulunamadı: {photo_path}")

    return FileResponse(path=str(photo_path), media_type=_media_type_for_image(photo_path))


# -----------------------------------------------------------------------------
# Mutasyon uçları: ADMIN-ONLY
# -----------------------------------------------------------------------------

@router.post("/system/{system_id}", response_model=SystemVariantOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_variant(
    system_id: UUID,
    payload: SystemVariantCreate,
    db: Session = Depends(get_db),
):
    """
    Verilen System için yeni SystemVariant oluşturur.
    """
    if not os.path.exists(VARIANT_PHOTO_DIR):
        os.makedirs(VARIANT_PHOTO_DIR, exist_ok=True)
    return create_system_variant(db, system_id, payload)

@router.put(
    "/{variant_id}/system",
    response_model=SystemVariantOut,
    summary="(ADMIN) Bir SystemVariant'ın bağlı olduğu System'i değiştir",
    dependencies=[Depends(get_current_admin)],
)
def reassign_variant_system_endpoint(
    variant_id: UUID,
    payload: SystemVariantReassignIn,
    db: Session = Depends(get_db),
):
    updated = reassign_variant_system(db, variant_id, payload.system_id)
    if not updated:
        # not-found / silinmiş / geçersiz hedef system
        raise HTTPException(status_code=400, detail="Variant veya hedef system bulunamadı / silinmiş.")
    return updated

@router.put("/{variant_id}", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def update_variant(
    variant_id: UUID,
    payload: SystemVariantUpdate,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    photo_path = os.path.join(BASE_DIR, obj.photo_url)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    update_system_variant(db, variant_id, SystemVariantUpdate(photo_url=None))

    return {"message": "Fotoğraf silindi"}


@router.post("/{variant_id}/pdf-photo", summary="Variant PDF foto çıktısı yükle/güncelle", dependencies=[Depends(get_current_admin)])
def upload_or_replace_variant_pdf_photo(
    variant_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    obj = get_system_variant(db, variant_id)
    if not obj:
        raise HTTPException(404, "Variant not found")

    if obj.pdf_foto_cikti:
        old_path = os.path.join(BASE_DIR, obj.pdf_foto_cikti)
        if os.path.exists(old_path):
            os.remove(old_path)

    if not os.path.exists(VARIANT_PHOTO_DIR):
        os.makedirs(VARIANT_PHOTO_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[-1]
    filename = f"{variant_id}_pdf{ext}"
    full_path = os.path.join(VARIANT_PHOTO_DIR, filename)

    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pdf_photo_url = f"variant_photos/{filename}"
    update_system_variant(db, variant_id, SystemVariantUpdate(pdf_foto_cikti=pdf_photo_url))

    return {
        "message": "PDF fotoğraf yüklendi/güncellendi",
        "pdf_foto_cikti": pdf_photo_url
    }


@router.delete("/{variant_id}/pdf-photo", summary="Variant PDF foto çıktısını sil", dependencies=[Depends(get_current_admin)])
def delete_variant_pdf_photo(
    variant_id: UUID,
    db: Session = Depends(get_db),
):
    obj = get_system_variant(db, variant_id)
    if not obj or not obj.pdf_foto_cikti:
        raise HTTPException(404, "PDF fotoğraf bulunamadı")

    photo_path = os.path.join(BASE_DIR, obj.pdf_foto_cikti)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    update_system_variant(db, variant_id, SystemVariantUpdate(pdf_foto_cikti=None))
    return {"message": "PDF fotoğraf silindi"}


@router.post("/", response_model=SystemVariantDetailOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_variant_with_templates_endpoint(
    payload: SystemVariantCreateWithTemplates,
    db: Session = Depends(get_db),
):
    """
    Yeni system variant oluşturur ve ilişkili profil, cam, malzeme şablonlarını ekler.
    """
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
    dependencies=[Depends(get_current_admin)],
)
def update_variant_templates_endpoint(
    variant_id: UUID,
    payload: SystemVariantUpdateWithTemplates,
    db: Session = Depends(get_db),
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


# -----------------------------------------------------------------------------
# ✅ VARYANT AKTİF/PASİF (ADMIN-ONLY)
# -----------------------------------------------------------------------------

@router.put("/{variant_id}/activate", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def activate_variant(
    variant_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Varyantı aktife alır. (Parent system pasifse yine de açılabilir; istersen burada kontrol ekleyebilirsin.)
    """
    v = get_system_variant(db, variant_id)
    if not v or v.is_deleted:
        raise HTTPException(status_code=404, detail="Variant not found")
    updated = update_system_variant(db, variant_id, SystemVariantUpdate(is_active=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated


@router.put("/{variant_id}/deactivate", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def deactivate_variant(
    variant_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Varyantı pasife alır.
    """
    v = get_system_variant(db, variant_id)
    if not v or v.is_deleted:
        raise HTTPException(status_code=404, detail="Variant not found")
    updated = update_system_variant(db, variant_id, SystemVariantUpdate(is_active=False))
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated

@router.put("/system/{system_id}/reorder", dependencies=[Depends(get_current_admin)])
def reorder_variants_of_system(
    system_id: UUID,
    payload: SystemVariantReorderIn,
    db: Session = Depends(get_db),
):
    """
    Admin: Belirli bir system'e ait varyantların sıralamasını toplu günceller.
    payload.items = [{id: UUID, sort_index: int}, ...]
    (İsteğe bağlı) payload.system_id gönderilmişse path param ile eşleşmeli.
    """
    if payload.system_id and payload.system_id != system_id:
        raise HTTPException(status_code=400, detail="Payload.system_id path ile uyuşmuyor")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Boş liste gönderilemez")

    ids = [it.id for it in payload.items]

    # Varlık ve sahiplik doğrulaması (hepsi aynı system'e ait ve silinmemiş olmalı)
    rows = (
        db.query(SystemVariant.id, SystemVariant.system_id)
        .filter(
            SystemVariant.id.in_(ids),
            SystemVariant.is_deleted == False,
        )
        .all()
    )
    found = {r[0]: r[1] for r in rows}
    missing = [str(i) for i in ids if i not in found]
    if missing:
        raise HTTPException(status_code=404, detail=f"Bulunamadı/silinmiş varyant id'ler: {', '.join(missing)}")

    wrong_parent = [str(i) for i in ids if found.get(i) != system_id]
    if wrong_parent:
        raise HTTPException(status_code=400, detail=f"Bu varyantlar verilen system'e ait değil: {', '.join(wrong_parent)}")

    # Güncelleme (transaction)
    for it in payload.items:
        db.query(SystemVariant).filter(SystemVariant.id == it.id).update(
            {"sort_index": int(it.sort_index)},
            synchronize_session=False
        )
    db.commit()

    return {"message": "Varyant sıralaması güncellendi", "updated": len(payload.items)}

@router.put("/{variant_id}/move", response_model=SystemVariantOut, dependencies=[Depends(get_current_admin)])
def move_variant(
    variant_id: UUID,
    direction: str = Query(..., regex="^(up|down)$", description='"up": bir üst sıradaki varyantla, "down": bir alt sıradaki ile yer değiştir'),
    steps: int = Query(1, ge=1, le=50),
    db: Session = Depends(get_db),
):
    v = get_system_variant(db, variant_id)
    if not v or v.is_deleted:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Sıralama aynı system içinde
    system_id = v.system_id

    for _ in range(steps):
        cur_idx = v.sort_index

        if direction == "up":
            neighbor = (
                db.query(SystemVariant)
                .filter(
                    SystemVariant.system_id == system_id,
                    SystemVariant.is_deleted == False,
                    SystemVariant.sort_index < cur_idx,
                )
                .order_by(desc(SystemVariant.sort_index))
                .first()
            )
        else:  # "down"
            neighbor = (
                db.query(SystemVariant)
                .filter(
                    SystemVariant.system_id == system_id,
                    SystemVariant.is_deleted == False,
                    SystemVariant.sort_index > cur_idx,
                )
                .order_by(asc(SystemVariant.sort_index))
                .first()
            )

        if not neighbor:
            # En üst/en alt, daha fazla hareket yok
            break

        neighbor_idx = neighbor.sort_index
        db.query(SystemVariant).filter(SystemVariant.id == v.id).update({"sort_index": neighbor_idx}, synchronize_session=False)
        db.query(SystemVariant).filter(SystemVariant.id == neighbor.id).update({"sort_index": cur_idx}, synchronize_session=False)
        db.flush()
        db.refresh(v)

    db.commit()
    db.refresh(v)
    return v
