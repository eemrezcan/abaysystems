# app/crud/project.py

from uuid import uuid4
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.project import (
    Project,
    ProjectSystem,
    ProjectSystemProfile,
    ProjectSystemGlass,
    ProjectSystemMaterial,
    ProjectExtraMaterial,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSystemsUpdate
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
        order_no=payload.order_no,
        order_date=payload.order_date,
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
            color=sys_req.color,
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


def get_projects(db: Session) -> List[Project]:
    return db.query(Project).all()


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: UUID, payload: ProjectUpdate) -> Optional[Project]:
    proj = get_project(db, project_id)
    if not proj:
        return None
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