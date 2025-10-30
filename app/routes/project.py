# app/routes/project.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from math import ceil

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser
from app.models.customer import Customer

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
    create_project_extra_remote,   # 🆕
    update_project_extra_remote,   # 🆕
    delete_project_extra_remote,   # 🆕
    update_project_code_by_number,
    update_project_system_glass_colors,
    bulk_update_project_system_glass_colors_dual,
    update_project_extra_glass_colors,
    bulk_update_project_extra_glass_colors_dual,
    bulk_update_system_glass_color_by_type,
    bulk_update_all_glass_colors_in_project,        # ⬅️ EKLE
    bulk_update_glass_colors_by_type_in_project,    # ⬅️ EKLE

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
    RemoteInProject,               # 🆕 requirements GET için
    ProjectExtraRemoteCreate,      # 🆕
    ProjectExtraRemoteUpdate,      # 🆕
    ProjectExtraRemoteOut,         # 🆕
    ProjectCodeUpdate,
    ProjectPricesUpdate,
    SystemGlassBulkByTypeIn,
    ProjectGlassColorAllIn,       # ⬅️ EKLE
    ProjectGlassColorByTypeIn,    # ⬅️ EKLE
    SingleGlassColorUpdate,
    ExtraGlassColorBulkUpdate,
)
from app.crud.project import _SENTINEL

from app.models.project import (
    Project,
    ProjectExtraProfile,
    ProjectExtraGlass,
    ProjectExtraMaterial,
    ProjectExtraRemote,
    ProjectSystemRemote,
    ProjectSystemGlass,     # 🆕 system glass join’ı için
    ProjectSystem,          # 🆕 security join zinciri için
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _attach_customer_name(db: Session, proj: Project) -> None:
    """Project ORM objesine customer_name alanını enjekte eder."""
    cust_name = None
    if getattr(proj, "customer_id", None):
        cust = db.query(Customer).filter(Customer.id == proj.customer_id).first()
        cust_name = getattr(cust, "name", None)
    setattr(proj, "customer_name", cust_name or "")

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
        proj = create_project(db, payload, created_by=current_user.id)
        _attach_customer_name(db, proj)  
        return ProjectOut.from_orm(proj)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ProjectPageOut)
def list_projects(
    name: str | None = Query(
        default=None,
        min_length=1,
        description="Proje adına göre filtre (contains, case-insensitive)"
    ),
    code: str | None = Query(
        default=None,
        min_length=1,
        description="Proje koduna göre filtre (contains, case-insensitive)"
    ),
    is_teklif: bool | None = Query(
        default=None,
        description=(
            "True → created_at DESC (son oluşturulan en üstte); "
            "False → approval_date DESC (son onaylanan en üstte). "
            "Boş bırakılırsa varsayılan sıralama: created_at DESC."
        ),
    ),
    # 🔽 Yeni filtre parametreleri
    paint_status: str | None = Query(
        default=None,
        description="Boya durumu (exact match). Örn: 'durum belirtilmedi', 'hazır', 'beklemede' vb."
    ),
    glass_status: str | None = Query(
        default=None,
        description="Cam durumu (exact match)."
    ),
    production_status: str | None = Query(
        default=None,
        description="Üretim durumu (exact match)."
    ),
    customer_id: UUID | None = Query(
        default=None,
        description="Belirli bir müşteri ID'sine ait projeler."
    ),
    # ✅ YENİ: sıralama bayrakları
    proje_sorted: bool | None = Query(
        default=None,
        description="True: projeler (is_teklif=False) artan sıralanır; False/None: mevcut ters sıralama."
    ),
    teklifler_sorted: bool | None = Query(
        default=None,
        description="True: teklifler (is_teklif=True) artan sıralanır; False/None: mevcut ters sıralama."
    ),
    # Sayfalama
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Sayfa başına kayıt (page size)"
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="1'den başlayan sayfa numarası"
    ),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Sadece oturumdaki kullanıcının projeleri.
    Filtreler:
      - name / code: contains (CI)
      - is_teklif: True/False → sıralama kuralı değişir
      - paint_status / glass_status / production_status: exact match
      - customer_id: eşleşen müşteri
    """
    offset = (page - 1) * limit

    items, total = get_projects_page(
        db=db,
        owner_id=current_user.id,
        name=name,
        code=code,
        limit=limit,
        offset=offset,
        is_teklif=is_teklif,
        paint_status=paint_status,
        glass_status=glass_status,
        production_status=production_status,
        customer_id=customer_id,
        # ✅ YENİ
        proje_sorted=proje_sorted,
        teklifler_sorted=teklifler_sorted,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    items_out = [ProjectOut.from_orm(x) for x in items]
    return ProjectPageOut(
        items=items_out,
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
    _attach_customer_name(db, proj)
    return ProjectOut.from_orm(proj)


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
    _attach_customer_name(db, proj) 
    return ProjectOut.from_orm(proj)


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
    _attach_customer_name(db, updated)  # ⬅️ EKLENDİ
    return ProjectOut.from_orm(updated)


@router.put("/{project_id}/code", response_model=ProjectOut)
def update_project_code_endpoint(
    project_id: UUID,
    payload: ProjectCodeUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Proje kodunu (prefix dahil) serbest metin olarak günceller.
    Benzersizlik Project.project_kodu üzerinden kontrol edilir.
    """
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        updated = update_project_code(db, project_id, new_code=payload.project_kodu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    _attach_customer_name(db, updated)
    return ProjectOut.from_orm(updated)


@router.put("/{project_id}/prices", response_model=ProjectOut)
def update_project_prices_endpoint(
    project_id: UUID,
    payload: ProjectPricesUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Yalnızca press_price ve painted_price alanlarını günceller.
    En az bir alan gönderilmelidir.
    """
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    # En az bir alan zorunlu
    if payload.press_price is None and payload.painted_price is None:
        raise HTTPException(status_code=400, detail="En az bir alan (press_price veya painted_price) gönderin.")

    # Var olan ortak update akışını kullan
    try:
        updated = update_project_all(
            db,
            project_id=project_id,
            payload=ProjectUpdate(
                press_price=payload.press_price,
                painted_price=payload.painted_price,
            ),
            owner_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    _attach_customer_name(db, updated)  # ⬅️ EKLENDİ
    return ProjectOut.from_orm(updated)


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
        proj = add_systems_to_project(db, project_id, payload)
        _attach_customer_name(db, proj)  # ⬅️ EKLENDİ
        return ProjectOut.from_orm(proj)
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
    _attach_customer_name(db, proj_updated)  # ⬅️ EKLENDİ
    return ProjectOut.from_orm(proj_updated)



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
                total_weight_kg=float(p.total_weight_kg) if p.total_weight_kg is not None else 0.0,
                order_index=p.order_index,
                is_painted=bool(getattr(p, "is_painted", False)),
            )
            for p in sys.profiles
        ]
        glasses: List[GlassInProject] = [
            GlassInProject(
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                area_m2=float(g.area_m2) if g.area_m2 is not None else 0.0,
                order_index=g.order_index,

                # 🔁 çift renk alanları
                glass_color_id_1=getattr(g, "glass_color_id_1", None),
                glass_color_1=getattr(g, "glass_color_text_1", None),
                glass_color_id_2=getattr(g, "glass_color_id_2", None),
                glass_color_2=getattr(g, "glass_color_text_2", None),
            )
            for g in sys.glasses
        ]
        materials: List[MaterialInProject] = [
            MaterialInProject(
                material_id=m.material_id,
                count=m.count,
                cut_length_mm=float(m.cut_length_mm) if m.cut_length_mm is not None else None,
                type=m.type,
                piece_length_mm=m.piece_length_mm,
                unit_price=float(m.unit_price) if m.unit_price is not None else None,
                order_index=m.order_index,
            )
            for m in sys.materials
        ]

        # 🆕 Kumandalar
        remotes: List[RemoteInProject] = [
            RemoteInProject(
                remote_id=r.remote_id,
                count=r.count,
                order_index=r.order_index,
                unit_price=float(r.unit_price) if r.unit_price is not None else None,
            )
            for r in sys.remotes
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
                remotes=remotes,
            )
        )

    extras_out: List[ExtraRequirement] = [
        ExtraRequirement(
            material_id=e.material_id,
            count=e.count,
            cut_length_mm=float(e.cut_length_mm) if e.cut_length_mm is not None else None,
            unit_price=float(e.unit_price) if e.unit_price is not None else None,
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
        proj = add_only_systems_to_project(db, project_id, payload.systems)
        _attach_customer_name(db, proj)  # ⬅️ EKLENDİ
        return ProjectOut.from_orm(proj)
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
        proj = add_only_extras_to_project(
            db,
            project_id,
            extras=payload.extra_requirements,
            extra_profiles=payload.extra_profiles,
            extra_glasses=payload.extra_glasses,
            extra_remotes=payload.extra_remotes,
        )
        _attach_customer_name(db, proj)  # ⬅️ EKLENDİ
        return ProjectOut.from_orm(proj)
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

# CREATE
@router.post("/extra-profiles", response_model=ProjectExtraProfileOut, status_code=201)
def add_extra_profile_endpoint(
    payload: ProjectExtraProfileCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        extra = create_project_extra_profile(
            db,
            project_id=payload.project_id,
            profile_id=payload.profile_id,
            cut_length_mm=payload.cut_length_mm,
            cut_count=payload.cut_count,
            is_painted=payload.is_painted,
            unit_price=getattr(payload, "unit_price", None),
        )
        # FastAPI pydantic ile kendisi serialize edecek
        return extra
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/extra-profiles/{extra_id}", response_model=ProjectExtraProfileOut)
def update_extra_profile_endpoint(
    extra_id: UUID,
    payload: ProjectExtraProfileUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
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
        is_painted=payload.is_painted,
        unit_price=getattr(payload, "unit_price", None),
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

# CREATE
@router.post("/extra-glasses", response_model=ProjectExtraGlassOut, status_code=201)
def add_extra_glass_endpoint(
    payload: ProjectExtraGlassCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        extra = create_project_extra_glass(
            db,
            project_id=payload.project_id,
            glass_type_id=payload.glass_type_id,
            width_mm=payload.width_mm,
            height_mm=payload.height_mm,
            count=payload.count,
            unit_price=getattr(payload, "unit_price", None),

            # 🔁 Çift cam rengi
            glass_color_id_1=getattr(payload, "glass_color_id_1", None),
            glass_color_1=getattr(payload, "glass_color_1", None),
            glass_color_id_2=getattr(payload, "glass_color_id_2", None),
            glass_color_2=getattr(payload, "glass_color_2", None),
        )
        return extra
    except ValueError:
        raise HTTPException(404, "Project not found")



@router.put("/extra-glasses/{extra_id}", response_model=ProjectExtraGlassOut)
def update_extra_glass_endpoint(
    extra_id: UUID,
    payload: ProjectExtraGlassUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    proj = (
        db.query(Project)
        .join(ProjectExtraGlass, ProjectExtraGlass.project_id == Project.id)
        .filter(ProjectExtraGlass.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    data = payload.dict(exclude_unset=True)
    updated = update_project_extra_glass(
        db,
        extra_id,
        width_mm=data.get("width_mm"),
        height_mm=data.get("height_mm"),
        count=data.get("count"),
        unit_price=data.get("unit_price"),
        # 🔁 çift renk
        glass_color_id_1=data.get("glass_color_id_1", _SENTINEL),  # _SENTINEL CRUD içinde tanımlı
        glass_color_1=data.get("glass_color_1", _SENTINEL),
        glass_color_id_2=data.get("glass_color_id_2", _SENTINEL),
        glass_color_2=data.get("glass_color_2", _SENTINEL),
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
        extra = create_project_extra_material(
            db,
            project_id=payload.project_id,
            material_id=payload.material_id,
            count=payload.count,
            cut_length_mm=payload.cut_length_mm,
            unit_price=payload.unit_price,  # 💲 eklendi
        )
        return ProjectExtraMaterialOut.from_orm(extra)
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
        unit_price=payload.unit_price,  # 💲 eklendi
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra material not found")
    return ProjectExtraMaterialOut.from_orm(updated)



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

# ───────── Extra Remote ─────────

@router.post("/extra-remotes", response_model=ProjectExtraRemoteOut, status_code=201)
def add_extra_remote_endpoint(
    payload: ProjectExtraRemoteCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra kumanda ekler."""
    proj = get_project(db, payload.project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    try:
        extra = create_project_extra_remote(
            db,
            project_id=payload.project_id,
            remote_id=payload.remote_id,
            count=payload.count,
            unit_price=payload.unit_price,
        )
        return ProjectExtraRemoteOut.from_orm(extra)
    except ValueError:
        raise HTTPException(404, "Project not found")


@router.put("/extra-remotes/{extra_id}", response_model=ProjectExtraRemoteOut)
def update_extra_remote_endpoint(
    extra_id: UUID,
    payload: ProjectExtraRemoteUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra kumanda günceller."""
    proj = (
        db.query(Project)
        .join(ProjectExtraRemote, ProjectExtraRemote.project_id == Project.id)
        .filter(ProjectExtraRemote.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_extra_remote(
        db,
        extra_id,
        count=payload.count,
        unit_price=payload.unit_price,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra remote not found")
    return ProjectExtraRemoteOut.from_orm(updated)


@router.delete("/extra-remotes/{extra_id}", status_code=204)
def delete_extra_remote_endpoint(
    extra_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Ekstra kumanda siler."""
    proj = (
        db.query(Project)
        .join(ProjectExtraRemote, ProjectExtraRemote.project_id == Project.id)
        .filter(ProjectExtraRemote.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    success = delete_project_extra_remote(db, extra_id)
    if not success:
        raise HTTPException(status_code=404, detail="Extra remote not found")
    return

# ───────── Glass color updates (SYSTEM) ─────────

@router.put("/{project_id}/system-glasses/{psg_id}/color")
def update_system_glass_color_endpoint(
    project_id: UUID,
    psg_id: UUID,
    payload: SingleGlassColorUpdate,  # ⬅️ ortak dual payload
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Tek bir ProjectSystemGlass satırının çift cam renklerini günceller.
    Gönderilmeyen alanlara dokunulmaz; None gönderilirse o taraf temizlenir.
    """
    # Güvenlik: kayıt gerçekten bu projeye ve kullanıcıya mı ait?
    proj = (
        db.query(Project)
        .join(ProjectSystem, ProjectSystem.project_id == Project.id)
        .join(ProjectSystemGlass, ProjectSystemGlass.project_system_id == ProjectSystem.id)
        .filter(Project.id == project_id, ProjectSystemGlass.id == psg_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    data = payload.dict(exclude_unset=True)
    updated = update_project_system_glass_colors(
        db,
        project_system_glass_id=psg_id,
        glass_color_id_1=data.get("glass_color_id_1", _SENTINEL),
        glass_color_1=data.get("glass_color_1", _SENTINEL),
        glass_color_id_2=data.get("glass_color_id_2", _SENTINEL),
        glass_color_2=data.get("glass_color_2", _SENTINEL),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="System glass not found")

    return {"ok": True, "id": str(psg_id)}


@router.put("/{project_id}/system-glasses/colors/bulk", response_model=dict)
def bulk_update_system_glass_colors_by_type_endpoint(
    project_id: UUID,
    payload: SystemGlassBulkByTypeIn,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Bir projede, verilen system_variant_id + glass_type_id kombinasyonuna uyan TÜM
    ProjectSystemGlass kayıtlarının 1. ve/veya 2. cam rengini topluca günceller.

    KURAL:
    - payload.glass_color_id_1 GÖNDERİLDİ ise (None olabilir): 1. renk set/temizle.
    - payload.glass_color_id_1 GÖNDERİLMEDİ ise: 1. renge DOKUNMA.
    - 2. renk için de aynı mantık.
    """
    # Sahiplik doğrulaması
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    data = payload.dict(exclude_unset=True)
    touch_1 = ("glass_color_id_1" in data)
    touch_2 = ("glass_color_id_2" in data)

    if not touch_1 and not touch_2:
        return {"updated": 0}

    affected = bulk_update_system_glass_color_by_type(
        db=db,
        project_id=project_id,
        system_variant_id=payload.system_variant_id,
        glass_type_id=payload.glass_type_id,
        update_1=touch_1,
        glass_color_id_1=data.get("glass_color_id_1", None),
        update_2=touch_2,
        glass_color_id_2=data.get("glass_color_id_2", None),
    )
    return {"updated": affected}




# ───────── Glass color updates (EXTRA) ─────────

@router.put("/extra-glasses/{extra_id}/color")
def update_extra_glass_color_endpoint(
    extra_id: UUID,
    payload: SingleGlassColorUpdate,  # ⬅️ ortak dual payload
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Tek bir ProjectExtraGlass satırının çift cam renklerini günceller.
    Gönderilmeyen alanlara dokunulmaz; None gönderilirse o taraf temizlenir.
    """
    proj = (
        db.query(Project)
        .join(ProjectExtraGlass, ProjectExtraGlass.project_id == Project.id)
        .filter(ProjectExtraGlass.id == extra_id)
        .first()
    )
    ensure_owner_or_404(proj, current_user.id, "created_by")

    data = payload.dict(exclude_unset=True)
    updated = update_project_extra_glass_colors(
        db,
        extra_glass_id=extra_id,
        glass_color_id_1=data.get("glass_color_id_1", _SENTINEL),
        glass_color_1=data.get("glass_color_1", _SENTINEL),
        glass_color_id_2=data.get("glass_color_id_2", _SENTINEL),
        glass_color_2=data.get("glass_color_2", _SENTINEL),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Extra glass not found")

    return {"ok": True, "id": str(extra_id)}


@router.put("/{project_id}/extra-glasses/colors/bulk")
def bulk_update_extra_glass_colors_endpoint(
    project_id: UUID,
    payload: ExtraGlassColorBulkUpdate,  # ⬅️ şemadan dual liste
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Birden fazla ProjectExtraGlass kaydını toplu günceller.
    Güvenlik: sadece bu project_id'ye ait satırlar güncellenir.
    """
    if not payload.items:
        return {"updated": 0}

    ids = [it.extra_glass_id for it in payload.items]

    valid_ids = set(
        r[0] for r in
        db.query(ProjectExtraGlass.id)
          .join(Project, ProjectExtraGlass.project_id == Project.id)
          .filter(Project.id == project_id, Project.created_by == current_user.id, ProjectExtraGlass.id.in_(ids))
          .all()
    )

    # Sadece geçerli kayıtları ve gönderilen alanları topla
    items_to_apply = []
    for it in payload.items:
        if it.extra_glass_id not in valid_ids:
            continue
        d = it.dict(exclude_unset=True)
        items_to_apply.append({
            "extra_glass_id": d["extra_glass_id"],
            **({ "glass_color_id_1": d["glass_color_id_1"] } if "glass_color_id_1" in d else {}),
            **({ "glass_color_1": d["glass_color_1"] } if "glass_color_1" in d else {}),
            **({ "glass_color_id_2": d["glass_color_id_2"] } if "glass_color_id_2" in d else {}),
            **({ "glass_color_2": d["glass_color_2"] } if "glass_color_2" in d else {}),
        })

    if not items_to_apply:
        return {"updated": 0}

    updated_count = bulk_update_project_extra_glass_colors_dual(db, items_to_apply)
    return {"updated": updated_count}


@router.put("/{project_id}/glasses/colors/all", response_model=dict)
def bulk_set_all_glass_colors_in_project_endpoint(
    project_id: UUID,
    payload: ProjectGlassColorAllIn,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Projede yer alan TÜM camların (sistem + ekstra) cam renklerini topluca ayarlar/temizler.

    KURAL:
    - payload.glass_color_id_1 GÖNDERİLDİ ise (None olabilir): 1. renk KURULUR/Temizlenir.
    - payload.glass_color_id_1 GÖNDERİLMEDİ ise: 1. renge DOKUNULMAZ.
    - payload.glass_color_id_2 için de aynı mantık.
    """
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    data = payload.dict(exclude_unset=True)
    touch_1 = ("glass_color_id_1" in data)
    touch_2 = ("glass_color_id_2" in data)

    # Her iki alan da gelmediyse yapılacak iş yok
    if not touch_1 and not touch_2:
        return {"system_updated": 0, "extra_updated": 0, "total": 0}

    result = bulk_update_all_glass_colors_in_project(
        db=db,
        project_id=project_id,
        update_1=touch_1,
        glass_color_id_1=data.get("glass_color_id_1", None),  # gönderildiyse değer (None=temizle)
        update_2=touch_2,
        glass_color_id_2=data.get("glass_color_id_2", None),  # gönderildiyse değer (None=temizle)
    )
    return result





@router.put("/{project_id}/glasses/colors/by-type", response_model=dict)
def bulk_set_glass_colors_by_type_in_project_endpoint(
    project_id: UUID,
    payload: ProjectGlassColorByTypeIn,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Projede, verilen glass_type_id'ye sahip tüm camların (sistem + ekstra) çift cam rengini ayarlar/temizler.
    """
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    result = bulk_update_glass_colors_by_type_in_project(
        db=db,
        project_id=project_id,
        glass_type_id=payload.glass_type_id,
        glass_color_id_1=payload.glass_color_id_1,
        glass_color_id_2=payload.glass_color_id_2,
    )
    return result





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
    # Sahiplik
    proj = get_project(db, project_id)
    ensure_owner_or_404(proj, current_user.id, "created_by")

    updated = update_project_system(db, project_id, project_system_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Project system not found")

    # Güncel tek sistemi detaylı modelle döndür
    details = get_project_requirements_detailed(db, project_id)
    target = next((s for s in details.systems if s.project_system_id == project_system_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Project system not found")
    return target



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
