# app/routes/system.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.crud.system import (
    create_system,
    get_systems,
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
)

router = APIRouter(prefix="/api", tags=["Systems"])

# ----- SYSTEM CRUD -----
@router.post("/systems", response_model=SystemOut, status_code=201)
def create_system_endpoint(
    payload: SystemCreate,
    db: Session = Depends(get_db)
):
    return create_system(db, payload)


@router.get("/systems", response_model=list[SystemOut])
def list_systems(db: Session = Depends(get_db)):
    return get_systems(db)


@router.get("/systems/{system_id}", response_model=SystemOut)
def get_system_endpoint(system_id: UUID, db: Session = Depends(get_db)):
    obj = get_system(db, system_id)
    if not obj:
        raise HTTPException(404, "System not found")
    return obj


@router.put("/systems/{system_id}", response_model=SystemOut)
def update_system_endpoint(
    system_id: UUID,
    payload: SystemUpdate,
    db: Session = Depends(get_db)
):
    obj = update_system(db, system_id, payload)
    if not obj:
        raise HTTPException(404, "System not found")
    return obj


@router.delete("/systems/{system_id}", status_code=204)
def delete_system_endpoint(system_id: UUID, db: Session = Depends(get_db)):
    deleted = delete_system(db, system_id)
    if not deleted:
        raise HTTPException(404, "System not found")
    return

# ----- FULL CREATE: SYSTEM + VARIANT + GLASS-CONFIG -----
@router.post("/systems/full", status_code=201)
def create_full_system_endpoint(
    payload: SystemFullCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni bir request’te tek seferde:
      1. system
      2. system_variant
      3. glass_configs (opsiyonel)
    oluşturur.
    """
    return create_system_full(db, payload)

# ----- TEMPLATE FETCH -----
@router.get(
    "/system-templates/{variant_id}",
    response_model=SystemTemplatesOut,
    summary="Fetch all templates for a system variant"
)
def fetch_system_templates(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    profiles, glasses, materials = get_system_templates(db, variant_id)
    return SystemTemplatesOut(
        profileTemplates=[
            ProfileTemplateOut(
                profile_id=tpl.profile_id,
                formula_cut_length=tpl.formula_cut_length,
                formula_cut_count=tpl.formula_cut_count
            ) for tpl in profiles
        ],
        glassTemplates=[
            GlassTemplateOut(
                glass_type_id=tpl.glass_type_id,
                formula_width=tpl.formula_width,
                formula_height=tpl.formula_height,
                formula_count=tpl.formula_count
            ) for tpl in glasses
        ],
        materialTemplates=[
            MaterialTemplateOut(
                material_id=tpl.material_id,
                formula_quantity=tpl.formula_quantity
            ) for tpl in materials
        ]
    )

@router.get(
    "/system-variants/{variant_id}",
    response_model=SystemVariantDetailOut,
    summary="Get a system variant and its template details"
)
def get_system_variant_detail_endpoint(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    variant = get_system_variant_detail(db, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="System variant not found")
    return variant

# ----- PROFILE TEMPLATE CRUD -----
@router.post("/system-templates/profiles", response_model=ProfileTemplateOut, status_code=201)
def create_profile_template_endpoint(
    payload: SystemProfileTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_profile_template(db, payload)


@router.put("/system-templates/profiles/{template_id}", response_model=ProfileTemplateOut)
def update_profile_template_endpoint(
    template_id: UUID,
    payload: SystemProfileTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_profile_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Profile template not found")
    return obj


@router.delete("/system-templates/profiles/{template_id}", status_code=204)
def delete_profile_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_profile_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Profile template not found")
    return

# ----- GLASS TEMPLATE CRUD -----
@router.post("/system-templates/glasses", response_model=GlassTemplateOut, status_code=201)
def create_glass_template_endpoint(
    payload: SystemGlassTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_glass_template(db, payload)


@router.put("/system-templates/glasses/{template_id}", response_model=GlassTemplateOut)
def update_glass_template_endpoint(
    template_id: UUID,
    payload: SystemGlassTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_glass_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Glass template not found")
    return obj


@router.delete("/system-templates/glasses/{template_id}", status_code=204)
def delete_glass_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_glass_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Glass template not found")
    return

# ----- MATERIAL TEMPLATE CRUD -----
@router.post("/system-templates/materials", response_model=MaterialTemplateOut, status_code=201)
def create_material_template_endpoint(
    payload: SystemMaterialTemplateCreate,
    db: Session = Depends(get_db)
):
    return create_material_template(db, payload)


@router.put("/system-templates/materials/{template_id}", response_model=MaterialTemplateOut)
def update_material_template_endpoint(
    template_id: UUID,
    payload: SystemMaterialTemplateUpdate,
    db: Session = Depends(get_db)
):
    obj = update_material_template(db, template_id, payload)
    if not obj:
        raise HTTPException(404, "Material template not found")
    return obj


@router.delete("/system-templates/materials/{template_id}", status_code=204)
def delete_material_template_endpoint(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = delete_material_template(db, template_id)
    if not deleted:
        raise HTTPException(404, "Material template not found")
    return
