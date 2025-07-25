from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID
import os, shutil

from fastapi.responses import FileResponse
from app.db.session import get_db
from app.crud import catalog as crud
from app.schemas.catalog import (
    ProfileCreate, ProfileOut,
    GlassTypeCreate, GlassTypeOut,
    OtherMaterialCreate, OtherMaterialOut
)

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

# ----- PROFILE CRUD -----
@router.post("/profiles", response_model=ProfileOut, status_code=201)
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

@router.get("/profiles", response_model=List[ProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return crud.get_profiles(db)

@router.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: UUID, db: Session = Depends(get_db)):
    obj = crud.get_profile(db, profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.put("/profiles/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: UUID, payload: ProfileCreate, db: Session = Depends(get_db)):
    obj = crud.update_profile(db, profile_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: UUID, db: Session = Depends(get_db)):
    crud.delete_profile(db, profile_id)
    return

# ----- PROFILE IMAGE HANDLING -----
IMAGE_DIR = "profile_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

@router.post("/profiles/{profile_id}/image", status_code=201)
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
def get_profile_image(profile_id: UUID, db: Session = Depends(get_db)):
    obj = crud.get_profile(db, profile_id)
    if not obj or not obj.profil_kesit_fotograf:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(obj.profil_kesit_fotograf)

@router.put("/profiles/{profile_id}/image")
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

@router.delete("/profiles/{profile_id}/image", status_code=204)
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

# ----- GLASS TYPE CRUD -----
@router.post("/glass-types", response_model=GlassTypeOut, status_code=201)
def create_glass_type(payload: GlassTypeCreate, db: Session = Depends(get_db)):
    return crud.create_glass_type(db, payload)

@router.get("/glass-types", response_model=List[GlassTypeOut])
def list_glass_types(db: Session = Depends(get_db)):
    return crud.get_glass_types(db)

@router.get("/glass-types/{glass_type_id}", response_model=GlassTypeOut)
def get_glass_type(glass_type_id: UUID, db: Session = Depends(get_db)):
    obj = crud.get_glass_type(db, glass_type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

@router.put("/glass-types/{glass_type_id}", response_model=GlassTypeOut)
def update_glass_type(glass_type_id: UUID, payload: GlassTypeCreate, db: Session = Depends(get_db)):
    obj = crud.update_glass_type(db, glass_type_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return obj

@router.delete("/glass-types/{glass_type_id}", status_code=204)
def delete_glass_type(glass_type_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_glass_type(db, glass_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Glass type not found")
    return

# ----- OTHER MATERIAL CRUD -----
@router.post("/other-materials", response_model=OtherMaterialOut, status_code=201)
def create_other_material(payload: OtherMaterialCreate, db: Session = Depends(get_db)):
    return crud.create_other_material(db, payload)

@router.get("/other-materials", response_model=List[OtherMaterialOut])
def list_other_materials(db: Session = Depends(get_db)):
    return crud.get_other_materials(db)

@router.get("/other-materials/{material_id}", response_model=OtherMaterialOut)
def get_other_material(material_id: UUID, db: Session = Depends(get_db)):
    obj = crud.get_other_material(db, material_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

@router.put("/other-materials/{material_id}", response_model=OtherMaterialOut)
def update_other_material(material_id: UUID, payload: OtherMaterialCreate, db: Session = Depends(get_db)):
    obj = crud.update_other_material(db, material_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Material not found")
    return obj

@router.delete("/other-materials/{material_id}", status_code=204)
def delete_other_material(material_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_other_material(db, material_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Material not found")
    return
