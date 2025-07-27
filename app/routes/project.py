# app/routes/project.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Tuple
from uuid import UUID

from app.db.session import get_db
from app.crud.project import (
    create_project,
    get_projects,
    get_project,
    update_project,
    delete_project,
    add_systems_to_project,
    update_systems_for_project,
    get_project_requirements,
    add_only_systems_to_project,
    add_only_extras_to_project,
    get_project_requirements_detailed,
    update_project_colors,
    update_project_code,
    create_project_extra_profile,
    update_project_extra_profile,
    delete_project_extra_profile,
    create_project_extra_glass,
    update_project_extra_glass,
    delete_project_extra_glass,
    create_project_extra_material,
    update_project_extra_material,
    delete_project_extra_material,
    list_project_extra_profiles,
    list_project_extra_glasses,
    list_project_extra_materials
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSystemsUpdate,
    ProjectOut,
    ProfileInProject,
    GlassInProject,
    MaterialInProject,
    SystemRequirement,
    ExtraRequirement,
    ProjectSystemRequirementIn,
    ProjectExtraRequirementIn,
    ProjectRequirementsDetailedOut,
    ProjectColorUpdate,
    ProjectCodeUpdate,
    ExtraProfileIn,
    ExtraGlassIn,
    ProjectExtraProfileCreate,
    ProjectExtraProfileUpdate,
    ProjectExtraProfileOut,
    ProjectExtraGlassCreate,
    ProjectExtraGlassUpdate,
    ProjectExtraGlassOut,
    ProjectExtraMaterialCreate,
    ProjectExtraMaterialUpdate,
    ProjectExtraMaterialOut,
    ProjectExtraProfileOut,
    ProjectExtraGlassOut,
    ProjectExtraMaterialOut

)
from app.models.project import ProjectSystem, ProjectExtraMaterial

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("/", response_model=ProjectOut, status_code=201)
def create_project_endpoint(payload: ProjectCreate, db: Session = Depends(get_db)):
    """
    Yeni proje oluşturur.
    Artık payload içinde project_name zorunludur.
    """
    return create_project(db, payload)

@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """Tüm projeleri listeler."""
    return get_projects(db)

@router.get("/{project_id}", response_model=ProjectOut)
def get_project_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    proj = get_project(db, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj

@router.put("/{project_id}", response_model=ProjectOut)
def update_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Var olan projeyi günceller.
    Artık project_name alanını da güncelleyebilirsiniz.
    """
    proj = update_project(db, project_id, payload)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj

@router.delete("/{project_id}", status_code=204)
def delete_project_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    """Projeyi siler."""
    if not delete_project(db, project_id):
        raise HTTPException(404, "Project not found")
    return

@router.put("/{project_id}/colors", response_model=ProjectOut)
def update_project_colors_endpoint(
    project_id: UUID,
    payload: ProjectColorUpdate,
    db: Session = Depends(get_db)
):
    updated = update_project_colors(
        db,
        project_id,
        profile_color_id=payload.profile_color_id,
        glass_color_id=payload.glass_color_id
    )
    if not updated:
        raise HTTPException(404, "Project not found")
    return updated

@router.put("/{project_id}/code", response_model=ProjectOut)
def update_project_code_endpoint(
    project_id: UUID,
    payload: ProjectCodeUpdate,
    db: Session = Depends(get_db)
):
    """
    Proje kodunu günceller. Aynı kod başka projede varsa hata verir.
    """
    try:
        updated = update_project_code(db, project_id, payload.project_kodu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return updated

@router.post("/{project_id}/requirements", response_model=ProjectOut)
def add_requirements_endpoint(
    project_id: UUID,
    payload: ProjectSystemsUpdate,
    db: Session = Depends(get_db)
):
    """Projeye sistem ve ekstra malzemeleri ekler."""
    return add_systems_to_project(db, project_id, payload)

@router.put("/{project_id}/requirements", response_model=ProjectOut)
def update_requirements_endpoint(
    project_id: UUID,
    payload: ProjectSystemsUpdate,
    db: Session = Depends(get_db)
):
    """Projeye ait sistem ve ekstra malzeme kayıtlarını günceller."""
    proj = update_systems_for_project(db, project_id, payload)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj

@router.get("/{project_id}/requirements", response_model=ProjectSystemsUpdate)
def list_requirements_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Belirtilen projeye ait sistem ve ekstra malzeme kayıtlarını alır.
    """
    systems, extras = get_project_requirements(db, project_id)
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    systems_out: List[SystemRequirement] = []
    for sys in systems:
        profiles: List[ProfileInProject] = [
            ProfileInProject(
                profile_id=p.profile_id,
                cut_length_mm=float(p.cut_length_mm),
                cut_count=p.cut_count,
                total_weight_kg=float(p.total_weight_kg),
            )
            for p in sys.profiles
        ]
        glasses: List[GlassInProject] = [
            GlassInProject(
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                area_m2=float(g.area_m2),
            )
            for g in sys.glasses
        ]
        materials: List[MaterialInProject] = [
            MaterialInProject(
                material_id=m.material_id,
                count=m.count,
                cut_length_mm=float(m.cut_length_mm) if m.cut_length_mm is not None else None,
            )
            for m in sys.materials
        ]
        systems_out.append(SystemRequirement(
            system_variant_id=sys.system_variant_id,
            width_mm=float(sys.width_mm),
            height_mm=float(sys.height_mm),
            quantity=sys.quantity,
            profiles=profiles,
            glasses=glasses,
            materials=materials,
        ))

    extras_out: List[ExtraRequirement] = [
        ExtraRequirement(
            material_id=e.material_id,
            count=e.count,
            cut_length_mm=float(e.cut_length_mm) if e.cut_length_mm is not None else None,
        )
        for e in extras
    ]

    return ProjectSystemsUpdate(systems=systems_out, extra_requirements=extras_out)

@router.post("/{project_id}/add-requirements", response_model=ProjectOut)
def add_only_systems_endpoint(
    project_id: UUID,
    payload: ProjectSystemRequirementIn,
    db: Session = Depends(get_db)
):
    """
    Sadece sistemleri projeye ekler.
    """
    return add_only_systems_to_project(db, project_id, payload.systems)


@router.post("/{project_id}/add-extra-requirements", response_model=ProjectOut)
def add_only_extras_endpoint(
    project_id: UUID,
    payload: ProjectExtraRequirementIn,
    db: Session = Depends(get_db)
):
    """
    Sadece ekstra malzeme, profil ve camları projeye ekler.
    """
    return add_only_extras_to_project(
        db,
        project_id,
        extras=payload.extra_requirements,
        extra_profiles=payload.extra_profiles,
        extra_glasses=payload.extra_glasses
    )

@router.get("/{project_id}/requirements-detailed", response_model=ProjectRequirementsDetailedOut)
def get_detailed_requirements_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Belirtilen projeye ait sistem + profil + cam + malzeme ve ekstra malzeme detaylarını 
    katalog bilgileri ile birlikte döndürür.
    """
    try:
        return get_project_requirements_detailed(db, project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")


# EKSTRA PROFİL EKLEME ------------------------

@router.post("/extra-profiles", response_model=ProjectExtraProfileOut, status_code=201)
def add_extra_profile_endpoint(
    payload: ProjectExtraProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Ekstra profil ekler.
    """
    return create_project_extra_profile(
        db,
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        cut_length_mm=payload.cut_length_mm,
        cut_count=payload.cut_count
    )


@router.put("/extra-profiles/{extra_id}", response_model=ProjectExtraProfileOut)
def update_extra_profile_endpoint(
    extra_id: UUID,
    payload: ProjectExtraProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Ekstra profil günceller.
    """
    updated = update_project_extra_profile(
        db,
        extra_id,
        cut_length_mm=payload.cut_length_mm,
        cut_count=payload.cut_count
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra profile not found")
    return updated


@router.delete("/extra-profiles/{extra_id}", status_code=204)
def delete_extra_profile_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Ekstra profil siler.
    """
    success = delete_project_extra_profile(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra profile not found")
    return

# EKSTRA CAM EKLEME ---------------------------------

@router.post("/extra-glasses", response_model=ProjectExtraGlassOut, status_code=201)
def add_extra_glass_endpoint(
    payload: ProjectExtraGlassCreate,
    db: Session = Depends(get_db)
):
    """
    Ekstra cam ekler.
    """
    return create_project_extra_glass(
        db,
        project_id=payload.project_id,
        glass_type_id=payload.glass_type_id,
        width_mm=payload.width_mm,
        height_mm=payload.height_mm,
        count=payload.count
    )


@router.put("/extra-glasses/{extra_id}", response_model=ProjectExtraGlassOut)
def update_extra_glass_endpoint(
    extra_id: UUID,
    payload: ProjectExtraGlassUpdate,
    db: Session = Depends(get_db)
):
    """
    Ekstra cam günceller.
    """
    updated = update_project_extra_glass(
        db,
        extra_id,
        width_mm=payload.width_mm,
        height_mm=payload.height_mm,
        count=payload.count
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra glass not found")
    return updated


@router.delete("/extra-glasses/{extra_id}", status_code=204)
def delete_extra_glass_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Ekstra cam siler.
    """
    success = delete_project_extra_glass(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra glass not found")
    return

# EKSTRA METARYAL EKLE ------------------------------
@router.post("/extra-materials", response_model=ProjectExtraMaterialOut, status_code=201)
def add_extra_material_endpoint(
    payload: ProjectExtraMaterialCreate,
    db: Session = Depends(get_db)
):
    """
    Ekstra malzeme ekler.
    """
    return create_project_extra_material(
        db,
        project_id=payload.project_id,
        material_id=payload.material_id,
        count=payload.count,
        cut_length_mm=payload.cut_length_mm
    )


@router.put("/extra-materials/{extra_id}", response_model=ProjectExtraMaterialOut)
def update_extra_material_endpoint(
    extra_id: UUID,
    payload: ProjectExtraMaterialUpdate,
    db: Session = Depends(get_db)
):
    """
    Ekstra malzeme günceller.
    """
    updated = update_project_extra_material(
        db,
        extra_id,
        count=payload.count,
        cut_length_mm=payload.cut_length_mm
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra material not found")
    return updated


@router.delete("/extra-materials/{extra_id}", status_code=204)
def delete_extra_material_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Ekstra malzeme siler.
    """
    success = delete_project_extra_material(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra material not found")
    return

#-----------------list--------------------------------------

@router.get("/{project_id}/extra-profiles", response_model=List[ProjectExtraProfileOut])
def list_extra_profiles_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Bir projeye ait tüm ekstra profilleri listeler.
    """
    extras = list_project_extra_profiles(db, project_id)
    if extras is None:
        raise HTTPException(404, "Project not found")
    return extras

@router.get("/{project_id}/extra-glasses", response_model=List[ProjectExtraGlassOut])
def list_extra_glasses_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Bir projeye ait tüm ekstra camları listeler.
    """
    extras = list_project_extra_glasses(db, project_id)
    if extras is None:
        raise HTTPException(404, "Project not found")
    return extras

@router.get("/{project_id}/extra-materials", response_model=List[ProjectExtraMaterialOut])
def list_extra_materials_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Bir projeye ait tüm ekstra malzemeleri listeler.
    """
    extras = list_project_extra_materials(db, project_id)
    if extras is None:
        raise HTTPException(404, "Project not found")
    return extras