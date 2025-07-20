#!/usr/bin/env python
import sys, os

# Proje kökünü Python path'e ekleyelim
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import delete
from app.db.session import SessionLocal
from app.models.project import (
    Project,
    ProjectSystem,
    ProjectSystemProfile,
    ProjectSystemGlass,
    ProjectSystemMaterial,
    ProjectExtraMaterial,
)

def main():
    db = SessionLocal()

    # 1) Test sistem detaylarını sil
    subq = db.query(ProjectSystem.id).filter(
        ProjectSystem.color == 'string',
        ProjectSystem.width_mm == 0,
        ProjectSystem.height_mm == 0
    ).subquery()
    db.execute(delete(ProjectSystemProfile).where(
        ProjectSystemProfile.project_system_id.in_(subq)
    ))
    db.execute(delete(ProjectSystemGlass).where(
        ProjectSystemGlass.project_system_id.in_(subq)
    ))
    db.execute(delete(ProjectSystemMaterial).where(
        ProjectSystemMaterial.project_system_id.in_(subq)
    ))
    db.execute(delete(ProjectSystem).where(
        ProjectSystem.id.in_(subq)
    ))

    # 2) Test ekstra malzemeleri ve projeleri sil
    proj_ids = [pid for (pid,) in db.query(Project.id).filter(
        Project.order_no == 'string'
    ).all()]
    if proj_ids:
        db.execute(delete(ProjectExtraMaterial).where(
            ProjectExtraMaterial.project_id.in_(proj_ids)
        ))
        db.execute(delete(Project).where(
            Project.id.in_(proj_ids)
        ))

    db.commit()
    db.close()
    print("Test verileri temizlendi.")

if __name__ == '__main__':
    main()
