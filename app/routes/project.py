# app/routes/project.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from math import ceil

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser

from app.utils.ownership import ensure_owner_or_404

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
    list_project_extra_materials,
    update_project_system,
    delete_project_system,
    update_project_all,
    get_projects_page, 
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
    SystemInProjectOut,
    ExtraRequirement,
    ProjectSystemRequirementIn,
    ProjectExtraRequirementIn,
    ProjectRequirementsDetailedOut,
    ProjectColorUpdate,
    ProjectCodeUpdate,
    ProjectExtraProfileCreate,
    ProjectExtraProfileUpdate,
    ProjectExtraProfileOut,
    ProjectExtraGlassCreate,
    ProjectExtraGlassUpdate,
    ProjectExtraGlassOut,
    ProjectExtraMaterialCreate,
    ProjectExtraMaterialUpdate,
    ProjectExtraMaterialOut,
    ProjectPageOut,
)

# Ek: Extra* sahiplik kontrolünde projeye join için Project ve Extra modellerine ihtiyacımız var
from app.models.project import Project, ProjectExtraProfile, ProjectExtraGlass, ProjectExtraMaterial

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ───────── Project CRUD ─────────

@router.post("/", response_model=ProjectOut, status_code=201)
def create_project_endpoint(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Yeni proje oluşturur. created_by = current_user.id
    Müşteri sahipliği doğrulanır (CRUD içinde).
    """
    try:
        return create_project(db, payload, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ProjectPageOut)  # 🟢 değişti
def list_projects(
    name: str | None = Query(
        default=None,
        min_length=1,
        description="Proje adına göre filtre (contains, case-insensitive)"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Sayfa başına kayıt (page size)"
    ),
    page: int = Query(                # 🟢 yeni
        default=1,
        ge=1,
        description="1'den başlayan sayfa numarası"
    ),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Sadece oturumdaki kullanıcının projeleri; en yeni → en eski sırada."""
    offset = (page - 1) * limit

    items, total = get_projects_page(
        db=db,
        owner_id=current_user.id,
        name=name,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return ProjectPageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )

@router.get("/{project_id}", response_model=ProjectOut)
def get_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    proj = get_project(db, project_id)   # CRUD imzası owner_id almıyor
    ensure_owner_or_404(proj, current_user.id, "created_by")
    return proj


@router.put("/{project_id}", response_model=ProjectOut)
def update_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Proje kodu + proje adı + müşteri + profil/cam renkleri (+ created_at) tek seferde güncellenir.
    Sahiplik kontrolü current_user.id ile yapılır (CRUD içinde).
    """
    try:
        proj = update_project_all(db, project_id, payload, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.delete("/{project_id}", status_code=204)
def delete_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Projeyi siler (sadece kendi projesi)."""
    if not delete_project(db, project_id, owner_id=current_user.id):
        raise HTTPException(404, "Project not found")
    return


# ───────── Tekil alan güncellemeleri ─────────

@router.put("/{project_id}/colors", response_model=ProjectOut)
def update_project_colors_endpoint(
    project_id: UUID,
    payload: ProjectColorUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_colors(
        db,
        project_id,
        profile_color_id=payload.profile_color_id,
        glass_color_id=payload.glass_color_id,
    )
    if not updated:
        raise HTTPException(404, "Project not found")
    return updated


@router.put("/{project_id}/code", response_model=ProjectOut)
def update_project_code_endpoint(
    project_id: UUID,
    payload: ProjectCodeUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        updated = update_project_code(db, project_id, payload.project_kodu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


# ───────── Requirements (Systems + Extras) ─────────

@router.post("/{project_id}/requirements", response_model=ProjectOut)
def add_requirements_endpoint(
    project_id: UUID,
    payload: ProjectSystemsUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Projeye sistem ve ekstra malzemeleri ekler."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return add_systems_to_project(db, project_id, payload)
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/{project_id}/requirements", response_model=ProjectOut)
def update_requirements_endpoint(
    project_id: UUID,
    payload: ProjectSystemsUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Projeye ait sistem ve ekstra malzeme kayıtlarını günceller."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        proj_updated = update_systems_for_project(db, project_id, payload)
    except ValueError:
        raise HTTPException(404, "Project not found")

    if not proj_updated:
        raise HTTPException(404, "Project not found")
    return proj_updated


@router.get("/{project_id}/requirements", response_model=ProjectSystemsUpdate)
def list_requirements_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Belirtilen projeye ait sistem ve ekstra malzeme kayıtlarını alır."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    systems, extras = get_project_requirements(db, project_id)

    systems_out: List[SystemRequirement] = []
    for sys in systems:
        profiles: List[ProfileInProject] = [
            ProfileInProject(
                profile_id=p.profile_id,
                cut_length_mm=float(p.cut_length_mm),
                cut_count=p.cut_count,
                total_weight_kg=float(p.total_weight_kg) if p.total_weight_kg is not None else None,
                order_index=p.order_index,
            )
            for p in sys.profiles
        ]
        glasses: List[GlassInProject] = [
            GlassInProject(
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                area_m2=float(g.area_m2) if g.area_m2 is not None else None,
                order_index=g.order_index,
            )
            for g in sys.glasses
        ]
        materials: List[MaterialInProject] = [
            MaterialInProject(
                material_id=m.material_id,
                count=m.count,
                cut_length_mm=float(m.cut_length_mm) if m.cut_length_mm is not None else None,
                order_index=m.order_index,
            )
            for m in sys.materials
        ]
        systems_out.append(
            SystemRequirement(
                system_variant_id=sys.system_variant_id,
                width_mm=float(sys.width_mm),
                height_mm=float(sys.height_mm),
                quantity=sys.quantity,
                profiles=profiles,
                glasses=glasses,
                materials=materials,
            )
        )

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
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Sadece sistemleri projeye ekler."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return add_only_systems_to_project(db, project_id, payload.systems)
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.post("/{project_id}/add-extra-requirements", response_model=ProjectOut)
def add_only_extras_endpoint(
    project_id: UUID,
    payload: ProjectExtraRequirementIn,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Sadece ekstra malzeme, profil ve camları projeye ekler."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return add_only_extras_to_project(
            db,
            project_id,
            extras=payload.extra_requirements,
            extra_profiles=payload.extra_profiles,
            extra_glasses=payload.extra_glasses,
        )
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.get("/{project_id}/requirements-detailed", response_model=ProjectRequirementsDetailedOut)
def get_detailed_requirements_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Sistem + profil + cam + malzeme + ekstra malzeme detayları (sadece kendi projesi)."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return get_project_requirements_detailed(db, project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")


# ───────── Extra Profile ─────────

@router.post("/extra-profiles", response_model=ProjectExtraProfileOut, status_code=201)
def add_extra_profile_endpoint(
    payload: ProjectExtraProfileCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra profil ekler."""
    # Sahiplik doğrulaması (payload.project_id)
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return create_project_extra_profile(
            db,
            project_id=payload.project_id,
            profile_id=payload.profile_id,
            cut_length_mm=payload.cut_length_mm,
            cut_count=payload.cut_count,
        )
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/extra-profiles/{extra_id}", response_model=ProjectExtraProfileOut)
def update_extra_profile_endpoint(
    extra_id: UUID,
    payload: ProjectExtraProfileUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra profil günceller."""
    # Sahiplik doğrulaması: extra_id -> project -> created_by
    proj = (
        db.query(Project)
        .join(ProjectExtraProfile, ProjectExtraProfile.project_id == Project.id)
        .filter(ProjectExtraProfile.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_extra_profile(
        db,
        extra_id,
        cut_length_mm=payload.cut_length_mm,
        cut_count=payload.cut_count,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra profile not found")
    return updated


@router.delete("/extra-profiles/{extra_id}", status_code=204)
def delete_extra_profile_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra profil siler."""
    # Sahiplik doğrulaması
    proj = (
        db.query(Project)
        .join(ProjectExtraProfile, ProjectExtraProfile.project_id == Project.id)
        .filter(ProjectExtraProfile.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    success = delete_project_extra_profile(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra profile not found")
    return


# ───────── Extra Glass ─────────

@router.post("/extra-glasses", response_model=ProjectExtraGlassOut, status_code=201)
def add_extra_glass_endpoint(
    payload: ProjectExtraGlassCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra cam ekler."""
    # Sahiplik doğrulaması
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return create_project_extra_glass(
            db,
            project_id=payload.project_id,
            glass_type_id=payload.glass_type_id,
            width_mm=payload.width_mm,
            height_mm=payload.height_mm,
            count=payload.count,
        )
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/extra-glasses/{extra_id}", response_model=ProjectExtraGlassOut)
def update_extra_glass_endpoint(
    extra_id: UUID,
    payload: ProjectExtraGlassUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra cam günceller."""
    # Sahiplik doğrulaması
    proj = (
        db.query(Project)
        .join(ProjectExtraGlass, ProjectExtraGlass.project_id == Project.id)
        .filter(ProjectExtraGlass.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_extra_glass(
        db,
        extra_id,
        width_mm=payload.width_mm,
        height_mm=payload.height_mm,
        count=payload.count,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra glass not found")
    return updated


@router.delete("/extra-glasses/{extra_id}", status_code=204)
def delete_extra_glass_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra cam siler."""
    # Sahiplik doğrulaması
    proj = (
        db.query(Project)
        .join(ProjectExtraGlass, ProjectExtraGlass.project_id == Project.id)
        .filter(ProjectExtraGlass.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    success = delete_project_extra_glass(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra glass not found")
    return


# ───────── Extra Material ─────────

@router.post("/extra-materials", response_model=ProjectExtraMaterialOut, status_code=201)
def add_extra_material_endpoint(
    payload: ProjectExtraMaterialCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra malzeme ekler."""
    # Sahiplik doğrulaması
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        return create_project_extra_material(
            db,
            project_id=payload.project_id,
            material_id=payload.material_id,
            count=payload.count,
            cut_length_mm=payload.cut_length_mm,
        )
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/extra-materials/{extra_id}", response_model=ProjectExtraMaterialOut)
def update_extra_material_endpoint(
    extra_id: UUID,
    payload: ProjectExtraMaterialUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra malzeme günceller."""
    # Sahiplik doğrulaması
    proj = (
        db.query(Project)
        .join(ProjectExtraMaterial, ProjectExtraMaterial.project_id == Project.id)
        .filter(ProjectExtraMaterial.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_extra_material(
        db,
        extra_id,
        count=payload.count,
        cut_length_mm=payload.cut_length_mm,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra material not found")
    return updated


@router.delete("/extra-materials/{extra_id}", status_code=204)
def delete_extra_material_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra malzeme siler."""
    # Sahiplik doğrulaması
    proj = (
        db.query(Project)
        .join(ProjectExtraMaterial, ProjectExtraMaterial.project_id == Project.id)
        .filter(ProjectExtraMaterial.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    success = delete_project_extra_material(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra material not found")
    return


# ───────── ProjectSystem güncelleme & silme ─────────

@router.put("/{project_id}/systems/{project_system_id}", response_model=SystemInProjectOut)
def update_project_system_endpoint(
    project_id: UUID,
    project_system_id: UUID,
    payload: SystemRequirement,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Belirli bir proje içi sistemi günceller."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_system(db, project_id, project_system_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Project system not found")
    return updated


@router.delete("/{project_id}/systems/{project_system_id}", status_code=204)
def delete_project_system_endpoint(
    project_id: UUID,
    project_system_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Belirli bir proje içi sistemi siler."""
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    success = delete_project_system(db, project_id, project_system_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project system not found")
    return
