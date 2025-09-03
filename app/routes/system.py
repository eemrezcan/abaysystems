# app/routes/system.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os, shutil
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi.responses import FileResponse
from pathlib import Path

from app.db.session import get_db

from math import ceil
from fastapi import Query  # zaten var olabilir

# 🔐 Rol kontrolleri
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 Model erişimleri (GET filtreleri için)
from app.models.system import System, SystemVariant

from app.crud.system import (
    create_system,
    get_systems,                 # not: listede kendi sorgumuzu da kullanacağız (filtre için)
    get_system,
    update_system,
    delete_system,
    get_system_templates,
    create_profile_template,
    update_profile_template,
    delete_profile_template,
    create_glass_template,
    update_glass_template,
    delete_glass_template,
    create_material_template,
    update_material_template,
    delete_material_template,
    create_system_full,
    get_system_variant_detail,
    get_systems_page,
    create_remote_template,
    update_remote_template,
    delete_remote_template,
)
from app.schemas.system import (
    SystemCreate,
    SystemUpdate,
    SystemOut,
    SystemFullCreate,
    SystemTemplatesOut,
    ProfileTemplateOut,
    SystemProfileTemplateCreate,
    SystemProfileTemplateUpdate,
    GlassTemplateOut,
    SystemGlassTemplateCreate,
    SystemGlassTemplateUpdate,
    MaterialTemplateOut,
    SystemMaterialTemplateCreate,
    SystemMaterialTemplateUpdate,
    SystemVariantDetailOut,
    SystemPageOut,
    RemoteTemplateOut,
    SystemRemoteTemplateCreate,
    SystemRemoteTemplateUpdate,
)

router = APIRouter(prefix="/api", tags=["Systems"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SYSTEM_PHOTO_DIR = os.path.join(BASE_DIR, "system_photos")

# -----------------------------------------------------------------------------
# SYSTEM - GET (bayi + admin), diğerleri admin-only
# -----------------------------------------------------------------------------

@router.post("/systems", response_model=SystemOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_system_endpoint(
    payload: SystemCreate,
    db: Session = Depends(get_db)
):
    return create_system(db, payload)


@router.get("/systems", response_model=SystemPageOut)
def list_systems(
    q: str | None = Query(None, description="İsme göre filtre (contains, case-insensitive)"),
    # 🟢 limit artık str kabul ediyor: "10" veya "all"
    limit: str = Query("50", description='Sayfa başına kayıt. "all" desteklenir.'),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")

    # 🟢 limit'i çöz: "all" → None (sınırsız), sayı → int (1..200 arası sınırla)
    limit_val = None if isinstance(limit, str) and limit.lower() == "all" else int(limit)
    if limit_val is not None:
        limit_val = max(1, min(limit_val, 200))
    offset = 0 if limit_val is None else (page - 1) * limit_val

    items, total = get_systems_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit_val,   # 🟢 None ise LIMIT uygulanmayacak (Adım 2)
        offset=offset,
    )

    if limit_val is None:
        # 🟢 "all" modunda tek sayfa mantığı
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

    return SystemPageOut(
        items=items,
        total=total,
        page=page_out,
        limit=effective_limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )




@router.get("/systems/{system_id}", response_model=SystemOut)
def get_system_endpoint(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = get_system(db, system_id)
    if not obj:
        raise HTTPException(404, "System not found")
    # Bayi unpublished/silinmiş görmesin
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_published):
        raise HTTPException(404, "System not found")
    return obj


@router.put("/systems/{system_id}", response_model=SystemOut, dependencies=[Depends(get_current_admin)])
def update_system_endpoint(
    system_id: UUID,
    payload: SystemUpdate,
    db: Session = Depends(get_db)
):
    obj = update_system(db, system_id, payload)
    if not obj:
        raise HTTPException(404, "System not found")
    return obj


@router.delete("/systems/{system_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_system_endpoint(system_id: UUID, db: Session = Depends(get_db)):
    deleted = delete_system(db, system_id)
    if not deleted:
        raise HTTPException(404, "System not found")
    return

# -----------------------------------------------------------------------------
# TEMPLATES - GET (bayi + admin), mutasyonlar admin-only
# -----------------------------------------------------------------------------

@router.get(
    "/system-templates/{variant_id}",
    response_model=SystemTemplatesOut,
    summary="Fetch all templates for a system variant"
)
def fetch_system_templates(
    variant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Bayi unpublished/silinmiş variant veya sistemin şablonlarını göremesin
    if current_user.role != "admin":
        v = (
            db.query(SystemVariant)
            .join(System, SystemVariant.system_id == System.id)
            .filter(
                SystemVariant.id == variant_id,
                SystemVariant.is_deleted == False,
                System.is_deleted == False,
                SystemVariant.is_published == True,
                System.is_published == True,
            )
            .first()
        )
        if not v:
            raise HTTPException(status_code=404, detail="System variant not found")
    else:
        # Admin için de en azından var mı kontrol edelim
        exists = db.query(SystemVariant).filter(SystemVariant.id == variant_id).first()
        if not exists:
            raise HTTPException(status_code=404, detail="System variant not found")

    profiles, glasses, materials, remotes = get_system_templates(db, variant_id)  # 🆕


    return SystemTemplatesOut(
        profileTemplates=[
            ProfileTemplateOut(
                profile_id=tpl.profile_id,
                formula_cut_length=tpl.formula_cut_length,
                formula_cut_count=tpl.formula_cut_count,
                order_index=tpl.order_index,
                profile=tpl.profile
            )
            for tpl in profiles
        ],
        glassTemplates=[
            GlassTemplateOut(
                glass_type_id=tpl.glass_type_id,
                formula_width=tpl.formula_width,
                formula_height=tpl.formula_height,
                formula_count=tpl.formula_count,
                order_index=tpl.order_index,
                glass_type=tpl.glass_type
            )
            for tpl in glasses
        ],
        materialTemplates=[
            MaterialTemplateOut(
                material_id=tpl.material_id,
                formula_quantity=tpl.formula_quantity,
                formula_cut_length=tpl.formula_cut_length,
                type=tpl.type,
                piece_length_mm=tpl.piece_length_mm,
                order_index=tpl.order_index,
                material=tpl.material
            )
            for tpl in materials
        ],
        remoteTemplates=[
            RemoteTemplateOut(
                remote_id=tpl.remote_id,
                order_index=tpl.order_index,
                created_at=tpl.created_at,
                remote=tpl.remote,
            )
            for tpl in remotes
        ],
    )


@router.get(
    "/system-variants/{variant_id}",
    response_model=SystemVariantDetailOut,
    summary="Get a system variant and its template details"
)
def get_system_variant_detail_endpoint(
    variant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    variant = get_system_variant_detail(db, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="System variant not found")

    # Bayi unpublished/silinmiş variant/sistem görmesin
    if current_user.role != "admin":
        # variant.system ilişkisi dönüyorsa bunu kontrol ediyoruz
        if getattr(variant, "is_deleted", False) or not getattr(variant, "is_published", False):
            raise HTTPException(status_code=404, detail="System variant not found")
        sys = getattr(variant, "system", None)
        if not sys or getattr(sys, "is_deleted", False) or not getattr(sys, "is_published", False):
            raise HTTPException(status_code=404, detail="System variant not found")

    return variant

# ----- PROFILE TEMPLATE CRUD (admin-only) -----
@router.post("/system-templates/profiles", response_model=ProfileTemplateOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_profile_template_endpoint(
    payload: SystemProfileTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_profile_template(db, payload)


@router.put("/system-templates/profiles/{template_id}", response_model=ProfileTemplateOut, dependencies=[Depends(get_current_admin)])
def update_profile_template_endpoint(
    template_id: UUID,
    payload: SystemProfileTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_profile_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Profile template not found")
    return obj


@router.delete("/system-templates/profiles/{template_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_profile_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_profile_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Profile template not found")
    return

# ----- GLASS TEMPLATE CRUD (admin-only) -----
@router.post("/system-templates/glasses", response_model=GlassTemplateOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_glass_template_endpoint(
    payload: SystemGlassTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_glass_template(db, payload)


@router.put("/system-templates/glasses/{template_id}", response_model=GlassTemplateOut, dependencies=[Depends(get_current_admin)])
def update_glass_template_endpoint(
    template_id: UUID,
    payload: SystemGlassTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_glass_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Glass template not found")
    return obj


@router.delete("/system-templates/glasses/{template_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_glass_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_glass_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Glass template not found")
    return

# ----- MATERIAL TEMPLATE CRUD (admin-only) -----
@router.post("/system-templates/materials", response_model=MaterialTemplateOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_material_template_endpoint(
    payload: SystemMaterialTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_material_template(db, payload)


@router.put("/system-templates/materials/{template_id}", response_model=MaterialTemplateOut, dependencies=[Depends(get_current_admin)])
def update_material_template_endpoint(
    template_id: UUID,
    payload: SystemMaterialTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_material_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Material template not found")
    return obj


@router.delete("/system-templates/materials/{template_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_material_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_material_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Material template not found")
    return

# ----- REMOTE TEMPLATE CRUD (admin-only) -----
@router.post(
    "/system-templates/remotes",
    response_model=RemoteTemplateOut,
    status_code=201,
    dependencies=[Depends(get_current_admin)],
)
def create_remote_template_endpoint(
    payload: SystemRemoteTemplateCreate,
    db: Session = Depends(get_db),
):
    return create_remote_template(db, payload)


@router.put(
    "/system-templates/remotes/{template_id}",
    response_model=RemoteTemplateOut,
    dependencies=[Depends(get_current_admin)],
)
def update_remote_template_endpoint(
    template_id: UUID,
    payload: SystemRemoteTemplateUpdate,
    db: Session = Depends(get_db),
):
    obj = update_remote_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Remote template not found")
    return obj


@router.delete(
    "/system-templates/remotes/{template_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin)],
)
def delete_remote_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_remote_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Remote template not found")
    return

# -----------------------------------------------------------------------------
# SYSTEM PHOTO - GET (bayi + admin), POST/DELETE admin-only
# -----------------------------------------------------------------------------

@router.post("/systems/{system_id}/photo", summary="System fotoğrafı yükle/güncelle", dependencies=[Depends(get_current_admin)])
def upload_or_replace_system_photo(
    system_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    obj = get_system(db, system_id)
    if not obj:
        raise HTTPException(404, "System not found")

    # Eski fotoğraf varsa sil
    if obj.photo_url:
        old_path = os.path.join(BASE_DIR, obj.photo_url)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Yeni fotoğrafı yükle
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{system_id}{ext}"
    full_path = os.path.join(SYSTEM_PHOTO_DIR, filename)

    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_url = f"system_photos/{filename}"
    update_system(db, system_id, SystemUpdate(photo_url=photo_url))

    return {
        "message": "Fotoğraf yüklendi/güncellendi",
        "photo_url": photo_url
    }


@router.delete("/systems/{system_id}/photo", summary="System fotoğrafını sil", dependencies=[Depends(get_current_admin)])
def delete_system_photo(
    system_id: UUID,
    db: Session = Depends(get_db)
):
    obj = get_system(db, system_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    photo_path = os.path.join(BASE_DIR, obj.photo_url)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    update_system(db, system_id, SystemUpdate(photo_url=None))

    return {"message": "Fotoğraf silindi"}


@router.get("/systems/{system_id}/photo", summary="Sisteme ait fotoğrafı döner")
def get_system_photo_file(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Veritabanından system nesnesini al
    obj = get_system(db, system_id)
    if not obj or not obj.photo_url:
        raise HTTPException(404, "Fotoğraf bilgisi bulunamadı")

    # Bayi unpublished/silinmiş sistemin fotoğrafını göremesin
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_published):
        raise HTTPException(404, "Fotoğraf bilgisi bulunamadı")

    # system_photos klasörünü proje kök dizinine göre belirle
    BASE_DIR_LOCAL = Path(__file__).resolve().parent.parent.parent
    SYSTEM_PHOTO_DIR_LOCAL = BASE_DIR_LOCAL / "system_photos"

    # Dosya adı sadece UUID.png (veya uzantısı neyse)
    filename = Path(obj.photo_url).name
    photo_path = SYSTEM_PHOTO_DIR_LOCAL / filename

    # Dosya gerçekten varsa göster
    if not photo_path.exists():
        raise HTTPException(404, f"Fotoğraf dosyası bulunamadı: {photo_path}")

    return FileResponse(path=str(photo_path), media_type="image/jpeg")

@router.put("/systems/{system_id}/publish", response_model=SystemOut, dependencies=[Depends(get_current_admin)])
def publish_system(
    system_id: UUID,
    db: Session = Depends(get_db),
):
    obj = get_system(db, system_id)
    if not obj or obj.is_deleted:
        raise HTTPException(status_code=404, detail="System not found")
    updated = update_system(db, system_id, SystemUpdate(is_published=True))
    if not updated:
        raise HTTPException(status_code=404, detail="System not found")
    return updated

@router.put("/systems/{system_id}/unpublish", response_model=SystemOut, dependencies=[Depends(get_current_admin)])
def unpublish_system(
    system_id: UUID,
    db: Session = Depends(get_db),
):
    obj = get_system(db, system_id)
    if not obj or obj.is_deleted:
        raise HTTPException(status_code=404, detail="System not found")
    updated = update_system(db, system_id, SystemUpdate(is_published=False))
    if not updated:
        raise HTTPException(status_code=404, detail="System not found")
    return updated
