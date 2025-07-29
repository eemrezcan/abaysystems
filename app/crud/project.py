# app/crud/project.py

from uuid import uuid4
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.system import SystemVariant, System
from app.models.profile import Profile
from app.models.glass_type import GlassType
from app.models.other_material import OtherMaterial
from app.schemas.project import ProjectRequirementsDetailedOut, SystemInProjectOut, ProfileInProjectOut, GlassInProjectOut, MaterialInProjectOut
from app.schemas.project import ExtraRequirement, ExtraProfileIn, ExtraGlassIn
from app.models.project import ProjectExtraMaterial, ProjectExtraProfile, ProjectExtraGlass
from app.models.customer import Customer

from app.models.project import (
    Project,
    ProjectSystem,
    ProjectSystemProfile,
    ProjectSystemGlass,
    ProjectSystemMaterial,
    ProjectExtraMaterial,
    ProjectExtraProfile,
    ProjectExtraGlass
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSystemsUpdate,
    SystemRequirement,
    ExtraRequirement,
    ExtraProfileIn,
    ExtraGlassIn,
    ExtraProfileDetailed,
    ExtraGlassDetailed
)


def _generate_project_code(db: Session) -> str:
    """
    Fetches the most recently created project's code, increments its numeric part,
    starting at 10000 if none or invalid.
    """
    last = db.query(Project).order_by(Project.created_at.desc()).first()
    if last and isinstance(last.project_kodu, str) and last.project_kodu.startswith("TALU-"):
        try:
            parts = last.project_kodu.split("-", 1)
            n = int(parts[1]) + 1
        except (ValueError, IndexError):
            n = 10000
    else:
        n = 10000
    return f"TALU-{n}"


def create_project(db: Session, payload: ProjectCreate) -> Project:
    """
    Creates a new Project with an auto-incremented project_kodu (TALU-xxxx).
    """
    code = _generate_project_code(db)
    project = Project(
        customer_id=payload.customer_id,
        project_name=payload.project_name,   # 🟢 Yeni eklenen alan
        created_by=payload.created_by,
        project_kodu=code,
        created_at=datetime.utcnow()
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def add_systems_to_project(
    db: Session,
    project_id: UUID,
    payload: ProjectSystemsUpdate
) -> Project:
    """
    Adds calculated systems and extra materials to an existing project.

    1) Look up project by ID, raise if not found.
    2) For each system requirement, create ProjectSystem and related child records.
    3) Create project-level extra material records.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # Create system entries
    for sys_req in payload.systems:
        ps = ProjectSystem(
            id=uuid4(),
            project_id=project.id,
            system_variant_id=sys_req.system_variant_id,
            width_mm=sys_req.width_mm,
            height_mm=sys_req.height_mm,
            quantity=sys_req.quantity
        )
        db.add(ps)
        db.flush()

        for p in sys_req.profiles:
            db.add(ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg
            ))

        for g in sys_req.glasses:
            db.add(ProjectSystemGlass(
                id=uuid4(),
                project_system_id=ps.id,
                glass_type_id=g.glass_type_id,
                width_mm=g.width_mm,
                height_mm=g.height_mm,
                count=g.count,
                area_m2=g.area_m2
            ))

        for m in sys_req.materials:
            db.add(ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count
            ))

    # Project-level extra requirements
    for extra in payload.extra_requirements:
        db.add(ProjectExtraMaterial(
            id=uuid4(),
            project_id=project.id,
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm
        ))

    db.commit()
    db.refresh(project)
    return project

def update_project_code(db: Session, project_id: UUID, new_code: str) -> Project | None:
    # Aynı project_kodu başka bir projede var mı?
    exists = (
        db.query(Project)
        .filter(Project.project_kodu == new_code, Project.id != project_id)
        .first()
    )
    if exists:
        raise ValueError("Bu proje kodu başka bir projede zaten kullanılıyor.")

    project = get_project(db, project_id)
    if not project:
        return None

    project.project_kodu = new_code
    db.commit()
    db.refresh(project)
    return project


def get_projects(db: Session) -> List[Project]:
    return db.query(Project).all()


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: UUID, payload: ProjectUpdate) -> Optional[Project]:
    proj = get_project(db, project_id)
    if not proj:
        return None
    # Proje tarihini (created_at) güncelleme desteği
    if payload.created_at is not None:
        proj.created_at = payload.created_at
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(proj, field, value)
    db.commit()
    db.refresh(proj)
    return proj


def delete_project(db: Session, project_id: UUID) -> bool:
    deleted = db.query(Project).filter(Project.id == project_id).delete()
    db.commit()
    return bool(deleted)


def update_systems_for_project(
    db: Session,
    project_id: UUID,
    payload: ProjectSystemsUpdate
) -> Optional[Project]:
    db.query(ProjectSystemProfile).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystemGlass).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystemMaterial).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.project_id == project_id).delete(synchronize_session=False)
    db.commit()

    return add_systems_to_project(db, project_id, payload)


def get_project_requirements(
    db: Session,
    project_id: UUID
) -> Tuple[List[ProjectSystem], List[ProjectExtraMaterial]]:
    """
    Verilen project_id’ye ait:
      - ProjectSystem kayıtlarını (ilişkili profiller, camlar, malzemeler yüklü olarak)
      - Ve ProjectExtraMaterial kayıtlarını
    döner.
    """
    systems = (
        db.query(ProjectSystem)
          .filter(ProjectSystem.project_id == project_id)
          .all()
    )
    extras = (
        db.query(ProjectExtraMaterial)
          .filter(ProjectExtraMaterial.project_id == project_id)
          .all()
    )
    return systems, extras

def add_only_systems_to_project(
    db: Session,
    project_id: UUID,
    systems: List[SystemRequirement]
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    for sys_req in systems:
        ps = ProjectSystem(
            id=uuid4(),
            project_id=project.id,
            system_variant_id=sys_req.system_variant_id,
            width_mm=sys_req.width_mm,
            height_mm=sys_req.height_mm,
            quantity=sys_req.quantity
        )
        db.add(ps)
        db.flush()

        for p in sys_req.profiles:
            db.add(ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg
            ))

        for g in sys_req.glasses:
            db.add(ProjectSystemGlass(
                id=uuid4(),
                project_system_id=ps.id,
                glass_type_id=g.glass_type_id,
                width_mm=g.width_mm,
                height_mm=g.height_mm,
                count=g.count,
                area_m2=g.area_m2
            ))

        for m in sys_req.materials:
            db.add(ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count
            ))

    db.commit()
    db.refresh(project)
    return project
def add_only_extras_to_project(
    db: Session,
    project_id: UUID,
    extras: List[ExtraRequirement],
    extra_profiles: List[ExtraProfileIn],
    extra_glasses: List[ExtraGlassIn]
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # Malzemeler
    for extra in extras:
        db.add(ProjectExtraMaterial(
            id=uuid4(),
            project_id=project.id,
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm
        ))

    # Profiller
    for profile in extra_profiles:
        db.add(ProjectExtraProfile(
            id=uuid4(),
            project_id=project.id,
            profile_id=profile.profile_id,
            cut_length_mm=profile.cut_length_mm,
            cut_count=profile.cut_count
        ))

    # Camlar
    for glass in extra_glasses:
        area_m2 = (glass.width_mm / 1000) * (glass.height_mm / 1000)  # isteğe bağlı hesap
        db.add(ProjectExtraGlass(
            id=uuid4(),
            project_id=project.id,
            glass_type_id=glass.glass_type_id,
            width_mm=glass.width_mm,
            height_mm=glass.height_mm,
            count=glass.count,
            area_m2=area_m2
        ))

    db.commit()
    db.refresh(project)
    return project

def get_project_requirements_detailed(
    db: Session,
    project_id: UUID
) -> ProjectRequirementsDetailedOut:
    """
    Verilen project_id’ye ait tüm sistem içeriklerini ve ekstra malzemeleri katalog bilgileriyle birlikte döndürür.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    customer = db.query(Customer).filter(Customer.id == project.customer_id).first()

    project_systems = (
        db.query(ProjectSystem)
        .filter(ProjectSystem.project_id == project_id)
        .all()
    )

    result_systems = []
    for ps in project_systems:
        # Sistem varyant ve üst sistem bilgisi
        variant = db.query(SystemVariant).filter(SystemVariant.id == ps.system_variant_id).first()
        system = db.query(System).filter(System.id == variant.system_id).first()

        # Profiller
        profiles_raw = (
            db.query(ProjectSystemProfile)
            .filter(ProjectSystemProfile.project_system_id == ps.id)
            .all()
        )
        profiles = [
            ProfileInProjectOut(
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg,
                profile=db.query(Profile).filter(Profile.id == p.profile_id).first()
            )
            for p in profiles_raw
        ]

        # Camlar
        glasses_raw = (
            db.query(ProjectSystemGlass)
            .filter(ProjectSystemGlass.project_system_id == ps.id)
            .all()
        )
        glasses = [
            GlassInProjectOut(
                glass_type_id=g.glass_type_id,
                width_mm=g.width_mm,
                height_mm=g.height_mm,
                count=g.count,
                area_m2=g.area_m2,
                glass_type=db.query(GlassType).filter(GlassType.id == g.glass_type_id).first()
            )
            for g in glasses_raw
        ]

        # Malzemeler
        materials_raw = (
            db.query(ProjectSystemMaterial)
            .filter(ProjectSystemMaterial.project_system_id == ps.id)
            .all()
        )
        materials = [
            MaterialInProjectOut(
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count,
                material=db.query(OtherMaterial).filter(OtherMaterial.id == m.material_id).first()
            )
            for m in materials_raw
        ]

        result_systems.append(
            SystemInProjectOut(
                project_system_id=ps.id, 
                system_variant_id=ps.system_variant_id,
                name=variant.name,
                system=system,
                width_mm=ps.width_mm,
                height_mm=ps.height_mm,
                quantity=ps.quantity,
                profiles=profiles,
                glasses=glasses,
                materials=materials
            )
        )

    # Proje seviyesi ekstra malzemeler
    extras_raw = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.project_id == project_id).all()
    extra_requirements = [
        MaterialInProjectOut(
            material_id=e.material_id,
            cut_length_mm=e.cut_length_mm,
            count=e.count,
            material=db.query(OtherMaterial).filter(OtherMaterial.id == e.material_id).first()
        )
        for e in extras_raw
    ]

        # --- ekstra profiller detaylı olarak yükle ---
    extra_profiles = []
    for p in db.query(ProjectExtraProfile).filter(ProjectExtraProfile.project_id == project_id).all():
        prof = db.query(Profile).filter(Profile.id == p.profile_id).first()
        extra_profiles.append(
            ExtraProfileDetailed(
                profile_id=p.profile_id,
                cut_length_mm=float(p.cut_length_mm),
                cut_count=p.cut_count,
                profile=prof
            )
        )

    # --- ekstra camlar detaylı olarak yükle ---
    extra_glasses = []
    for g in db.query(ProjectExtraGlass).filter(ProjectExtraGlass.project_id == project_id).all():
        gt = db.query(GlassType).filter(GlassType.id == g.glass_type_id).first()
        extra_glasses.append(
            ExtraGlassDetailed(
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                glass_type=gt
            )
        )





    return ProjectRequirementsDetailedOut(
        id=project.id,
        customer=customer,
        profile_color=project.profile_color,  # 🆕 renk objesi
        glass_color=project.glass_color,      # 🆕 renk objesi
        systems=result_systems,
        extra_requirements=extra_requirements,
        extra_profiles=extra_profiles,
        extra_glasses=extra_glasses,

    )

def update_project_colors(
    db: Session,
    project_id: UUID,
    profile_color_id: Optional[UUID],
    glass_color_id: Optional[UUID]
) -> Project | None:
    project = get_project(db, project_id)
    if not project:
        return None
    project.profile_color_id = profile_color_id
    project.glass_color_id = glass_color_id
    db.commit()
    db.refresh(project)
    return project

# ───────── Extra Profile CRUD ─────────

def create_project_extra_profile(
    db: Session,
    project_id: UUID,
    profile_id: UUID,
    cut_length_mm: float,
    cut_count: int
) -> ProjectExtraProfile:
    extra = ProjectExtraProfile(
        id=uuid4(),
        project_id=project_id,
        profile_id=profile_id,
        cut_length_mm=cut_length_mm,
        cut_count=cut_count
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    return extra


def update_project_extra_profile(
    db: Session,
    extra_id: UUID,
    cut_length_mm: Optional[float] = None,
    cut_count: Optional[int] = None
) -> Optional[ProjectExtraProfile]:
    extra = db.query(ProjectExtraProfile).filter(ProjectExtraProfile.id == extra_id).first()
    if not extra:
        return None

    if cut_length_mm is not None:
        extra.cut_length_mm = cut_length_mm
    if cut_count is not None:
        extra.cut_count = cut_count

    db.commit()
    db.refresh(extra)
    return extra


def delete_project_extra_profile(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraProfile).filter(ProjectExtraProfile.id == extra_id).delete()
    db.commit()
    return bool(deleted)

# ───────── Extra Glass CRUD ─────────

def create_project_extra_glass(
    db: Session,
    project_id: UUID,
    glass_type_id: UUID,
    width_mm: float,
    height_mm: float,
    count: int
) -> ProjectExtraGlass:
    area_m2 = (width_mm / 1000) * (height_mm / 1000)
    extra = ProjectExtraGlass(
        id=uuid4(),
        project_id=project_id,
        glass_type_id=glass_type_id,
        width_mm=width_mm,
        height_mm=height_mm,
        count=count,
        area_m2=area_m2
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    return extra


def update_project_extra_glass(
    db: Session,
    extra_id: UUID,
    width_mm: Optional[float] = None,
    height_mm: Optional[float] = None,
    count: Optional[int] = None
) -> Optional[ProjectExtraGlass]:
    extra = db.query(ProjectExtraGlass).filter(ProjectExtraGlass.id == extra_id).first()
    if not extra:
        return None

    if width_mm is not None:
        extra.width_mm = width_mm
    if height_mm is not None:
        extra.height_mm = height_mm
    if count is not None:
        extra.count = count

    # area_m2 yeniden hesapla
    if width_mm or height_mm:
        extra.area_m2 = (extra.width_mm / 1000) * (extra.height_mm / 1000)

    db.commit()
    db.refresh(extra)
    return extra


def delete_project_extra_glass(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraGlass).filter(ProjectExtraGlass.id == extra_id).delete()
    db.commit()
    return bool(deleted)

# ───────── Extra Material CRUD ─────────

def create_project_extra_material(
    db: Session,
    project_id: UUID,
    material_id: UUID,
    count: int,
    cut_length_mm: Optional[float] = None
) -> ProjectExtraMaterial:
    extra = ProjectExtraMaterial(
        id=uuid4(),
        project_id=project_id,
        material_id=material_id,
        count=count,
        cut_length_mm=cut_length_mm
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    return extra


def update_project_extra_material(
    db: Session,
    extra_id: UUID,
    count: Optional[int] = None,
    cut_length_mm: Optional[float] = None
) -> Optional[ProjectExtraMaterial]:
    extra = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.id == extra_id).first()
    if not extra:
        return None

    if count is not None:
        extra.count = count
    if cut_length_mm is not None:
        extra.cut_length_mm = cut_length_mm

    db.commit()
    db.refresh(extra)
    return extra


def delete_project_extra_material(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.id == extra_id).delete()
    db.commit()
    return bool(deleted)


# ───────── List Extra CRUD ─────────

def list_project_extra_profiles(db: Session, project_id: UUID) -> List[ProjectExtraProfile]:
    return (
        db.query(ProjectExtraProfile)
          .filter(ProjectExtraProfile.project_id == project_id)
          .all()
    )

def list_project_extra_glasses(db: Session, project_id: UUID) -> List[ProjectExtraGlass]:
    return (
        db.query(ProjectExtraGlass)
          .filter(ProjectExtraGlass.project_id == project_id)
          .all()
    )

def list_project_extra_materials(db: Session, project_id: UUID) -> List[ProjectExtraMaterial]:
    return (
        db.query(ProjectExtraMaterial)
          .filter(ProjectExtraMaterial.project_id == project_id)
          .all()
    )

# ───────── ProjectSystem CRUD ─────────
def update_project_system(
    db: Session,
    project_id: UUID,
    project_system_id: UUID,
    payload: SystemRequirement
) -> Optional[ProjectSystem]:
    """
    Belirli bir project_system kaydını günceller (ölçüler ve içerik).
    """
    ps = (
        db.query(ProjectSystem)
          .filter(
             ProjectSystem.id == project_system_id,
             ProjectSystem.project_id == project_id
          )
          .first()
    )
    if not ps:
        return None

    # Temel alanlar
    ps.width_mm  = payload.width_mm
    ps.height_mm = payload.height_mm
    ps.quantity  = payload.quantity

    # Önce mevcut child kayıtları sil
    db.query(ProjectSystemProfile).filter(ProjectSystemProfile.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemGlass).filter(ProjectSystemGlass.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemMaterial).filter(ProjectSystemMaterial.project_system_id == project_system_id).delete(synchronize_session=False)

    # Yeniden ekle
    for p in payload.profiles:
        db.add(ProjectSystemProfile(
            id=uuid4(),
            project_system_id=ps.id,
            profile_id=p.profile_id,
            cut_length_mm=p.cut_length_mm,
            cut_count=p.cut_count,
            total_weight_kg=p.total_weight_kg
        ))
    for g in payload.glasses:
        db.add(ProjectSystemGlass(
            id=uuid4(),
            project_system_id=ps.id,
            glass_type_id=g.glass_type_id,
            width_mm=g.width_mm,
            height_mm=g.height_mm,
            count=g.count,
            area_m2=g.area_m2
        ))
    for m in payload.materials:
        db.add(ProjectSystemMaterial(
            id=uuid4(),
            project_system_id=ps.id,
            material_id=m.material_id,
            cut_length_mm=m.cut_length_mm,
            count=m.count
        ))

    db.commit()
    db.refresh(ps)
    return ps

def delete_project_system(
    db: Session,
    project_id: UUID,
    project_system_id: UUID
) -> bool:
    """
    Belirli bir project_system kaydını ve ilgili alt kayıtları siler.
    """
    # Child kayıtları sil
    db.query(ProjectSystemProfile).filter(ProjectSystemProfile.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemGlass).filter(ProjectSystemGlass.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemMaterial).filter(ProjectSystemMaterial.project_system_id == project_system_id).delete(synchronize_session=False)

    # ProjectSystem kaydını sil
    deleted = (
        db.query(ProjectSystem)
          .filter(
             ProjectSystem.id == project_system_id,
             ProjectSystem.project_id == project_id
          )
          .delete()
    )
    db.commit()
    return bool(deleted)
