#app/routes/catalog.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID
import os, shutil

from math import ceil                              # 🟢
from fastapi import Query 

from fastapi.responses import FileResponse
from app.db.session import get_db

# 🔐 roller
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 modeller (bayi GET filtreleri için)
from app.models.profile import Profile
from app.models.glass_type import GlassType
from app.models.other_material import OtherMaterial

from app.crud import catalog as crud
from app.schemas.catalog import (                  # 🟢
    ProfileCreate, ProfileOut, ProfilePageOut,
    GlassTypeCreate, GlassTypeUpdate, GlassTypeOut, GlassTypePageOut,
    OtherMaterialCreate, OtherMaterialOut, OtherMaterialPageOut,
    RemoteCreate, RemoteOut, RemotePageOut
)
from app.crud.catalog import (
    get_profiles_page, get_glass_types_page, get_other_materials_page, get_remotes_page,
    set_profile_active, set_glass_type_active, set_other_material_active, set_remote_active  # ✅ eklendi
)


router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

# ----- PROFILE CRUD -----

@router.post("/profiles", response_model=ProfileOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    # Duplicate profil_kodu check
    if crud.get_profile_by_code(db, payload.profil_kodu):
        raise HTTPException(
            status_code=400,
            detail=f"Profile with kod '{payload.profil_kodu}' already exists"
        )
    try:
        return crud.create_profile(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create profile due to database constraint"
        )

@router.get("/profiles", response_model=ProfilePageOut)
def list_profiles(
    q: str | None = Query(None, description="Profil kodu/ismine göre filtre (contains, case-insensitive)"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_profiles_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return ProfilePageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )


@router.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = crud.get_profile(db, profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Bayi: silinmiş veya pasif profil göremez
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_active):
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.put("/profiles/{profile_id}", response_model=ProfileOut, dependencies=[Depends(get_current_admin)])
def update_profile(profile_id: UUID, payload: ProfileCreate, db: Session = Depends(get_db)):
    obj = crud.update_profile(db, profile_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.delete("/profiles/{profile_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_profile(profile_id: UUID, db: Session = Depends(get_db)):
    crud.delete_profile(db, profile_id)
    return

# ----- PROFILE IMAGE HANDLING -----
IMAGE_DIR = "profile_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR, exist_ok=True)

@router.post("/profiles/{profile_id}/image", status_code=201, dependencies=[Depends(get_current_admin)])
def upload_profile_image(profile_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    obj = crud.get_profile(db, profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    ext = os.path.splitext(file.filename)[1]
    filename = f"{obj.profil_kodu}{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    obj.profil_kesit_fotograf = filepath
    db.commit()
    db.refresh(obj)
    return {"filename": filename}

@router.get("/profiles/{profile_id}/image")
def get_profile_image(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = crud.get_profile(db, profile_id)
    if not obj or not obj.profil_kesit_fotograf:
        raise HTTPException(status_code=404, detail="Image not found")
    # Bayi: silinmiş/pasif profilin görselini göremez
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_active):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(obj.profil_kesit_fotograf)

@router.put("/profiles/{profile_id}/image", dependencies=[Depends(get_current_admin)])
def update_profile_image(profile_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    obj = crud.get_profile(db, profile_id)
    if not obj or not obj.profil_kesit_fotograf:
        raise HTTPException(status_code=404, detail="Profile or image not found")
    old_path = obj.profil_kesit_fotograf
    if os.path.exists(old_path):
        os.remove(old_path)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{obj.profil_kodu}{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    obj.profil_kesit_fotograf = filepath
    db.commit()
    db.refresh(obj)
    return {"filename": filename}

@router.delete("/profiles/{profile_id}/image", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_profile_image(profile_id: UUID, db: Session = Depends(get_db)):
    obj = crud.get_profile(db, profile_id)
    if not obj or not obj.profil_kesit_fotograf:
        raise HTTPException(status_code=404, detail="Profile or image not found")
    path = obj.profil_kesit_fotograf
    if os.path.exists(path):
        os.remove(path)
    obj.profil_kesit_fotograf = None
    db.commit()
    return

# ----- PROFILE ACTIVATE/DEACTIVATE -----

@router.put("/profiles/{profile_id}/activate", response_model=ProfileOut, dependencies=[Depends(get_current_admin)])
def activate_profile(profile_id: UUID, db: Session = Depends(get_db)):
    obj = set_profile_active(db, profile_id, True)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.put("/profiles/{profile_id}/deactivate", response_model=ProfileOut, dependencies=[Depends(get_current_admin)])
def deactivate_profile(profile_id: UUID, db: Session = Depends(get_db)):
    obj = set_profile_active(db, profile_id, False)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

# ----- GLASS TYPE CRUD -----

@router.post("/glass-types", response_model=GlassTypeOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_glass_type(payload: GlassTypeCreate, db: Session = Depends(get_db)):
    return crud.create_glass_type(db, payload)

@router.get("/glass-types", response_model=GlassTypePageOut)
def list_glass_types(
    q: str | None = Query(None, description="Cam ismine göre filtre (contains, case-insensitive)"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_glass_types_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return GlassTypePageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )


@router.get("/glass-types/{glass_type_id}", response_model=GlassTypeOut)
def get_glass_type(
    glass_type_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = crud.get_glass_type(db, glass_type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_active):
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

@router.put("/glass-types/{glass_type_id}", response_model=GlassTypeOut, dependencies=[Depends(get_current_admin)])
def update_glass_type(glass_type_id: UUID, payload: GlassTypeUpdate, db: Session = Depends(get_db)):
    obj = crud.update_glass_type(db, glass_type_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

@router.delete("/glass-types/{glass_type_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_glass_type(glass_type_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_glass_type(db, glass_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return

# ----- GLASS TYPE ACTIVATE/DEACTIVATE -----

@router.put("/glass-types/{glass_type_id}/activate", response_model=GlassTypeOut, dependencies=[Depends(get_current_admin)])
def activate_glass_type(glass_type_id: UUID, db: Session = Depends(get_db)):
    obj = set_glass_type_active(db, glass_type_id, True)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

@router.put("/glass-types/{glass_type_id}/deactivate", response_model=GlassTypeOut, dependencies=[Depends(get_current_admin)])
def deactivate_glass_type(glass_type_id: UUID, db: Session = Depends(get_db)):
    obj = set_glass_type_active(db, glass_type_id, False)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

# ----- OTHER MATERIAL CRUD -----

@router.post("/other-materials", response_model=OtherMaterialOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_other_material(payload: OtherMaterialCreate, db: Session = Depends(get_db)):
    return crud.create_other_material(db, payload)

@router.get("/other-materials", response_model=OtherMaterialPageOut)
def list_other_materials(
    q: str | None = Query(None, description="Diğer malzeme adına göre filtre (contains, case-insensitive)"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_other_materials_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return OtherMaterialPageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )


@router.get("/other-materials/{material_id}", response_model=OtherMaterialOut)
def get_other_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = crud.get_other_material(db, material_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_active):
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

@router.put("/other-materials/{material_id}", response_model=OtherMaterialOut, dependencies=[Depends(get_current_admin)])
def update_other_material(material_id: UUID, payload: OtherMaterialCreate, db: Session = Depends(get_db)):
    obj = crud.update_other_material(db, material_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

@router.delete("/other-materials/{material_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_other_material(material_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_other_material(db, material_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Material not found")
    return

# ----- OTHER MATERIAL ACTIVATE/DEACTIVATE -----

@router.put("/other-materials/{material_id}/activate", response_model=OtherMaterialOut, dependencies=[Depends(get_current_admin)])
def activate_other_material(material_id: UUID, db: Session = Depends(get_db)):
    obj = set_other_material_active(db, material_id, True)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

@router.put("/other-materials/{material_id}/deactivate", response_model=OtherMaterialOut, dependencies=[Depends(get_current_admin)])
def deactivate_other_material(material_id: UUID, db: Session = Depends(get_db)):
    obj = set_other_material_active(db, material_id, False)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

# ----- REMOTE (KUMANDA) CRUD -----

@router.post("/remotes", response_model=RemoteOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_remote(payload: RemoteCreate, db: Session = Depends(get_db)):
    return crud.create_remote(db, payload)

@router.get("/remotes", response_model=RemotePageOut)
def list_remotes(
    q: str | None = Query(None, description="Kumanda adına göre filtre (contains, case-insensitive)"),
    limit: int = Query(50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_remotes_page(
        db=db,
        is_admin=is_admin,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if limit > 0 else 0

    return RemotePageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )


@router.get("/remotes/{remote_id}", response_model=RemoteOut)
def get_remote(
    remote_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    obj = crud.get_remote(db, remote_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Remote not found")
    # admin değilse silinmiş/inaktif kayıt görülmesin
    if current_user.role != "admin" and (obj.is_deleted or not obj.is_active):
        raise HTTPException(status_code=404, detail="Remote not found")
    return obj


@router.put("/remotes/{remote_id}", response_model=RemoteOut, dependencies=[Depends(get_current_admin)])
def update_remote(remote_id: UUID, payload: RemoteCreate, db: Session = Depends(get_db)):
    obj = crud.update_remote(db, remote_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Remote not found")
    return obj


@router.delete("/remotes/{remote_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_remote(remote_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_remote(db, remote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Remote not found")
    return

# ----- REMOTE ACTIVATE/DEACTIVATE -----

@router.put("/remotes/{remote_id}/activate", response_model=RemoteOut, dependencies=[Depends(get_current_admin)])
def activate_remote(remote_id: UUID, db: Session = Depends(get_db)):
    obj = set_remote_active(db, remote_id, True)
    if not obj:
        raise HTTPException(status_code=404, detail="Remote not found")
    return obj

@router.put("/remotes/{remote_id}/deactivate", response_model=RemoteOut, dependencies=[Depends(get_current_admin)])
def deactivate_remote(remote_id: UUID, db: Session = Depends(get_db)):
    obj = set_remote_active(db, remote_id, False)
    if not obj:
        raise HTTPException(status_code=404, detail="Remote not found")
    return obj
