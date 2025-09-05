# app/crud/project.py

from uuid import uuid4
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.system import SystemVariant, System
from app.models.profile import Profile
from app.models.glass_type import GlassType
from app.models.other_material import OtherMaterial
from app.models.remote import Remote  # 🆕
from app.crud.project_code import issue_next_code_in_tx
from sqlalchemy.exc import IntegrityError
from app.models.project_code_rule import ProjectCodeRule

from app.models.project import (
    Project,
    ProjectSystem,
    ProjectSystemProfile,
    ProjectSystemGlass,
    ProjectSystemMaterial,
    ProjectExtraMaterial,
    ProjectExtraProfile,
    ProjectExtraGlass,
    ProjectSystemRemote,
    ProjectExtraRemote
)
from app.models.customer import Customer
from app.models.system_profile_template import SystemProfileTemplate
from app.models.system_glass_template   import SystemGlassTemplate
from app.models.system_material_template import SystemMaterialTemplate
from app.models.system_remote_template import SystemRemoteTemplate 

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSystemsUpdate,
    SystemRequirement,
    ExtraRequirement,
    ExtraProfileIn,
    ExtraGlassIn,
    ExtraProfileDetailed,
    ExtraGlassDetailed,
    ProjectRequirementsDetailedOut,
    SystemInProjectOut,
    ProfileInProjectOut,
    GlassInProjectOut,
    MaterialInProjectOut,
    ExtraRemoteIn,           # 🆕
    ExtraRemoteDetailed,     # 🆕
    RemoteInProjectOut,
)

# ------------------------------------------------------------
# PDF yardımcıları
# ------------------------------------------------------------

PDF_MAP_IN = {
    "camCiktisi": "cam_ciktisi",
    "profilAksesuarCiktisi": "profil_aksesuar_ciktisi",
    "boyaCiktisi": "boya_ciktisi",
    "siparisCiktisi": "siparis_ciktisi",
    "optimizasyonDetayliCiktisi": "optimizasyon_detayli_ciktisi",
    "optimizasyonDetaysizCiktisi": "optimizasyon_detaysiz_ciktisi",
}

def _apply_pdf(obj: Any, pdf_model_or_dict: Any) -> None:
    """CREATE/UPDATE sırasında payload.pdf geldiyse ORM kolonlarına uygular."""
    if not pdf_model_or_dict:
        return
    if hasattr(pdf_model_or_dict, "dict"):
        data = pdf_model_or_dict.dict(exclude_unset=True)
    elif isinstance(pdf_model_or_dict, dict):
        data = pdf_model_or_dict
    else:
        return
    for k, v in data.items():
        col = PDF_MAP_IN.get(k)
        if col is not None and v is not None:
            setattr(obj, col, bool(v))

def _pdf_from_obj(obj: Any) -> dict:
    """GET tarafında ORM objesinden camelCase pdf sözlüğü üret."""
    return {
        "camCiktisi":                  bool(getattr(obj, "cam_ciktisi", True)),
        "profilAksesuarCiktisi":      bool(getattr(obj, "profil_aksesuar_ciktisi", True)),
        "boyaCiktisi":                bool(getattr(obj, "boya_ciktisi", True)),
        "siparisCiktisi":             bool(getattr(obj, "siparis_ciktisi", True)),
        "optimizasyonDetayliCiktisi": bool(getattr(obj, "optimizasyon_detayli_ciktisi", True)),
        "optimizasyonDetaysizCiktisi":bool(getattr(obj, "optimizasyon_detaysiz_ciktisi", True)),
    }

# ------------------------------------------------------------
# Yardımcılar
# ------------------------------------------------------------

# def _generate_project_code(db: Session, owner_id: UUID) -> str:
#     """
#     Kullanıcıya özel artan proje kodu üretir.
#     Son projeyi created_by=owner_id filtresiyle bulur; TALU-xxxxx formatındaki numarayı arttırır.
#     Bulunamazsa 10000'dan başlar.
#     """
#     last = (
#         db.query(Project)
#           .filter(Project.created_by == owner_id)
#           .order_by(Project.created_at.desc())
#           .first()
#     )
#     if last and isinstance(last.project_kodu, str) and last.project_kodu.startswith("TALU-"):
#         try:
#             n = int(last.project_kodu.split("-", 1)[1]) + 1
#         except (ValueError, IndexError):
#             n = 10000
#     else:
#         n = 10000
#     return f"TALU-{n}"
def _format_code_from_rule(rule: ProjectCodeRule, number: int) -> str:
    if rule.padding and rule.padding > 0:
        return f"{rule.prefix}{rule.separator}{number:0{rule.padding}d}"
    return f"{rule.prefix}{rule.separator}{number}"

def _get_owner_rule(db: Session, owner_id: UUID) -> ProjectCodeRule | None:
    return db.query(ProjectCodeRule).filter(
        ProjectCodeRule.owner_id == owner_id,
        ProjectCodeRule.is_active == True
    ).first()

# ------------------------------------------------------------
# Proje CRUD
# ------------------------------------------------------------

def create_project(db: Session, payload: ProjectCreate, created_by: UUID) -> Project:
    # 1) Bir sonraki proje kodunu al (kilitli) - commit YOK
    next_n, code = issue_next_code_in_tx(db, created_by)

    # 2) Proje kaydını oluştur
    project = Project(
        id=uuid4(),
        customer_id=payload.customer_id,
        project_name=payload.project_name,
        created_by=created_by,
        project_kodu=code,
        created_at=datetime.utcnow(),
    )
    db.add(project)

    # 3) Tek commit
    try:
        db.commit()
    except IntegrityError:
        # Uç senaryoda unique çakışma olursa bir kez daha dene
        db.rollback()
        next_n, code = issue_next_code_in_tx(db, created_by)
        project.project_kodu = code
        db.add(project)
        db.commit()

    db.refresh(project)
    return project


def get_projects(
    db: Session,
    owner_id: UUID,
    name: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,  # 🟢 yeni
) -> list[Project]:
    """
    Kendi projelerini, en yeniden eskiye sıralı döndürür.
    İsteğe bağlı olarak 'name' (contains, case-insensitive) filtresi,
    'offset' ve 'limit' uygular (klasik sayfalama).
    """
    query = (
        db.query(Project)
        .filter(Project.created_by == owner_id)
        .order_by(Project.created_at.desc())
    )

    if name:
        like_val = f"%{name.lower()}%"
        query = query.filter(func.lower(Project.project_name).like(like_val))

    # 🟢 offset önce uygulanır
    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()

def get_projects_page(
    db: Session,
    owner_id: UUID,
    name: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Project], int]:
    """
    Filtrelenmiş toplam kayıt sayısı + sayfadaki kayıtları birlikte döndürür.
    """
    base_q = db.query(Project).filter(Project.created_by == owner_id)

    if name:
        like_val = f"%{name.lower()}%"
        base_q = base_q.filter(func.lower(Project.project_name).like(like_val))

    # Toplam (limit/offset uygulanmadan)
    total = base_q.order_by(None).count()

    # Sayfa verisi
    items = (
        base_q.order_by(Project.created_at.desc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    """
    Tekil proje (sahiplik kontrolü route katmanında yapılır).
    """
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: UUID, payload: ProjectUpdate) -> Optional[Project]:
    proj = get_project(db, project_id)
    if not proj:
        return None

    # created_at güncellemesi isteğe bağlı
    if payload.created_at is not None:
        proj.created_at = payload.created_at

    for field, value in payload.dict(exclude_unset=True).items():
        # id / created_by korumasına gerek yoksa schema zaten içermez
        setattr(proj, field, value)

    db.commit()
    db.refresh(proj)
    return proj

def update_project_code_by_number(
    db: Session,
    project_id: UUID,
    owner_id: UUID,
    new_number: int
) -> Optional[Project]:
    proj = get_project(db, project_id)
    if not proj:
        return None

    rule = _get_owner_rule(db, owner_id)
    if not rule:
        raise ValueError("Önce proje kodu kuralınızı oluşturun.")

    new_code = _format_code_from_rule(rule, new_number)

    # ✅ SADECE TAM KODA GÖRE (prefix+sep+number) global benzersizlik
    exists = (
        db.query(Project)
        .filter(Project.project_kodu == new_code, Project.id != project_id)
        .first()
    )
    if exists:
        # mesajı da global doğasına uygunlaştırdık
        raise ValueError("Bu proje kodu (prefix+numara) zaten kullanılıyor.")

    proj.project_kodu = new_code
    db.commit()
    db.refresh(proj)
    return proj

def update_project_all(
    db: Session,
    project_id: UUID,
    payload: ProjectUpdate,              # ProjectUpdate
    owner_id: UUID,
) -> Optional[Project]:
    # Proje sahibine ait mi?
    proj = (
        db.query(Project)
          .filter(Project.id == project_id, Project.created_by == owner_id)
          .first()
    )
    if not proj:
        return None

    # Müşteri değişiyorsa; o müşteri de bu kullanıcıya (bayiye/admin’e) ait ve silinmemiş olmalı
    if payload.customer_id is not None and payload.customer_id != proj.customer_id:
        cust = (
            db.query(Customer)
              .filter(
                  Customer.id == payload.customer_id,
                  Customer.dealer_id == owner_id,
                  Customer.is_deleted == False,
              )
              .first()
        )
        if not cust:
            raise ValueError("Customer not found or not owned by you.")

    if payload.project_number is not None:
        rule = _get_owner_rule(db, owner_id)
        if not rule:
            raise ValueError("Önce proje kodu kuralınızı oluşturun.")
        new_code = _format_code_from_rule(rule, payload.project_number)

        exists = (
            db.query(Project)
            .filter(Project.project_kodu == new_code, Project.id != project_id)
            .first()
        )
        if exists:
            raise ValueError("Bu proje kodu (prefix+numara) zaten kullanılıyor.")

        proj.project_kodu = new_code


    # Diğer alanlar (unset olanları dokunma; None gönderdiyse temizlemeye izin verelim)
    data = payload.dict(exclude_unset=True)

    # Zaten yukarıda ayrı ele aldık:
    data.pop("project_kodu", None)

    # created_at açıkça gönderildiyse güncelle
    if "created_at" in data:
        proj.created_at = data["created_at"]

    # isim / müşteri / renkler
    if "project_name" in data:
        proj.project_name = data["project_name"]
    if "customer_id" in data:
        proj.customer_id = data["customer_id"]
    if "profile_color_id" in data:
        proj.profile_color_id = data["profile_color_id"]  # None gelirse temizler
    if "glass_color_id" in data:
        proj.glass_color_id = data["glass_color_id"]      # None gelirse temizler

    db.commit()
    db.refresh(proj)
    return proj

def delete_project(db: Session, project_id: UUID, owner_id: Optional[UUID] = None) -> bool:
    """
    Hard delete. owner_id verilirse sahiplik filtresi de uygulanır.
    """
    q = db.query(Project).filter(Project.id == project_id)
    if owner_id is not None:
        q = q.filter(Project.created_by == owner_id)
    deleted = q.delete()
    db.commit()
    return bool(deleted)


def update_project_code(db: Session, project_id: UUID, new_code: str) -> Optional[Project]:
    # Benzersizlik kontrolü (global)
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

# ------------------------------------------------------------
# Gereksinimler (sistem + ekstra)
# ------------------------------------------------------------

def add_systems_to_project(
    db: Session,
    project_id: UUID,
    payload: ProjectSystemsUpdate
) -> Project:
    """
    Projeye sistemleri ve ekstra malzemeleri ekler.
    NOT: Extra requirements artık sistem döngüsünün DIŞINDA ekleniyor (bug fix).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # --- Sistemler
    for sys_req in payload.systems:
        ps = ProjectSystem(
            id=uuid4(),
            project_id=project.id,
            system_variant_id=sys_req.system_variant_id,
            width_mm=sys_req.width_mm,
            height_mm=sys_req.height_mm,
            quantity=sys_req.quantity,
        )
        db.add(ps)
        db.flush()

        # Şablonlara göre order_index haritaları
        tpl_profiles = {
            t.profile_id: t.order_index
            for t in db.query(SystemProfileTemplate)
                       .filter(SystemProfileTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }
        tpl_glasses = {
            t.glass_type_id: t.order_index
            for t in db.query(SystemGlassTemplate)
                       .filter(SystemGlassTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }
        tpl_materials = {
            t.material_id: t
            for t in db.query(SystemMaterialTemplate)
                    .filter(SystemMaterialTemplate.system_variant_id == sys_req.system_variant_id)
                    .all()
        }

        # Profiller
        for p in sys_req.profiles:
            obj = ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg,
                order_index=tpl_profiles.get(p.profile_id),
            )
            _apply_pdf(obj, getattr(p, "pdf", None))
            db.add(obj)

        # Camlar
        for g in sys_req.glasses:
            obj = ProjectSystemGlass(
                id=uuid4(),
                project_system_id=ps.id,
                glass_type_id=g.glass_type_id,
                width_mm=g.width_mm,
                height_mm=g.height_mm,
                count=g.count,
                area_m2=g.area_m2,
                order_index=tpl_glasses.get(g.glass_type_id),
            )
            _apply_pdf(obj, getattr(g, "pdf", None))
            db.add(obj)

        # Malzemeler
        for m in sys_req.materials:
            tpl = tpl_materials.get(m.material_id)  # SystemMaterialTemplate objesi (veya None)

            typ = m.type
            if typ is None and tpl is not None:
                typ = tpl.type

            piece_len = m.piece_length_mm
            if piece_len is None and tpl is not None:
                piece_len = tpl.piece_length_mm

            obj = ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count,
                type=typ,                         # ✅ yeni
                piece_length_mm=piece_len,        # ✅ yeni
                order_index=(tpl.order_index if tpl is not None else None),
            )
            _apply_pdf(obj, getattr(m, "pdf", None))
            db.add(obj)

        # 🔌 Kumandalar (SystemRemoteTemplate sırasına göre)
        tpl_remotes = {
            t.remote_id: t.order_index
            for t in db.query(SystemRemoteTemplate)
                       .filter(SystemRemoteTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }

        for r in getattr(sys_req, "remotes", []) or []:
            # unit_price girilmemişse katalogdaki fiyattan snapshot al
            unit_price = r.unit_price
            if unit_price is None:
                rem = db.query(Remote).filter(Remote.id == r.remote_id).first()
                unit_price = float(rem.price) if rem and rem.price is not None else None

            obj = ProjectSystemRemote(
                id=uuid4(),
                project_system_id=ps.id,
                remote_id=r.remote_id,
                count=r.count,
                unit_price=unit_price,
                order_index=tpl_remotes.get(r.remote_id),
            )
            _apply_pdf(obj, getattr(r, "pdf", None))
            db.add(obj)

    # --- Proje seviyesi ekstra malzemeler (DÖNGÜ DIŞI) 🔧
    for extra in payload.extra_requirements:
        obj = ProjectExtraMaterial(
            id=uuid4(),
            project_id=project.id,
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm,
        )
        _apply_pdf(obj, getattr(extra, "pdf", None))
        db.add(obj)

    db.commit()
    db.refresh(project)
    return project


def update_systems_for_project(
    db: Session,
    project_id: UUID,
    payload: ProjectSystemsUpdate
) -> Optional[Project]:
    # mevcut tüm içerikleri sil
    db.query(ProjectSystemProfile).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystemGlass).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystemMaterial).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectSystemRemote).join(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)  # 🆕
    db.query(ProjectSystem).filter(ProjectSystem.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.project_id == project_id).delete(synchronize_session=False)
    db.commit()

    return add_systems_to_project(db, project_id, payload)


def get_project_requirements(
    db: Session,
    project_id: UUID
) -> Tuple[List[ProjectSystem], List[ProjectExtraMaterial]]:
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
            quantity=sys_req.quantity,
        )
        db.add(ps)
        db.flush()

        tpl_profiles = {
            t.profile_id: t.order_index
            for t in db.query(SystemProfileTemplate)
                       .filter(SystemProfileTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }
        tpl_glasses = {
            t.glass_type_id: t.order_index
            for t in db.query(SystemGlassTemplate)
                       .filter(SystemGlassTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }
        tpl_materials = {
            t.material_id: t
            for t in db.query(SystemMaterialTemplate)
                    .filter(SystemMaterialTemplate.system_variant_id == sys_req.system_variant_id)
                    .all()
        }

        # Profiller
        for p in sys_req.profiles:
            obj = ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg,
                order_index=tpl_profiles.get(p.profile_id),
            )
            _apply_pdf(obj, getattr(p, "pdf", None))
            db.add(obj)

        # Camlar
        for g in sys_req.glasses:
            obj = ProjectSystemGlass(
                id=uuid4(),
                project_system_id=ps.id,
                glass_type_id=g.glass_type_id,
                width_mm=g.width_mm,
                height_mm=g.height_mm,
                count=g.count,
                area_m2=g.area_m2,
                order_index=tpl_glasses.get(g.glass_type_id),
            )
            _apply_pdf(obj, getattr(g, "pdf", None))
            db.add(obj)

        for m in sys_req.materials:
            tpl = tpl_materials.get(m.material_id)

            typ = m.type if m.type is not None else (tpl.type if tpl else None)
            piece_len = m.piece_length_mm if m.piece_length_mm is not None else (tpl.piece_length_mm if tpl else None)

            obj = ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count,
                type=typ,                       # ✅
                piece_length_mm=piece_len,      # ✅
                order_index=(tpl.order_index if tpl else None),
            )
            _apply_pdf(obj, getattr(m, "pdf", None))
            db.add(obj)

        # 🔌 Kumandalar
        tpl_remotes = {
            t.remote_id: t.order_index
            for t in db.query(SystemRemoteTemplate)
                       .filter(SystemRemoteTemplate.system_variant_id == sys_req.system_variant_id)
                       .all()
        }

        for r in getattr(sys_req, "remotes", []) or []:
            unit_price = r.unit_price
            if unit_price is None:
                rem = db.query(Remote).filter(Remote.id == r.remote_id).first()
                unit_price = float(rem.price) if rem and rem.price is not None else None

            obj = ProjectSystemRemote(
                id=uuid4(),
                project_system_id=ps.id,
                remote_id=r.remote_id,
                count=r.count,
                unit_price=unit_price,
                order_index=tpl_remotes.get(r.remote_id),
            )
            _apply_pdf(obj, getattr(r, "pdf", None))
            db.add(obj)

    db.commit()
    db.refresh(project)
    return project


def add_only_extras_to_project(
    db: Session,
    project_id: UUID,
    extras: List[ExtraRequirement],
    extra_profiles: List[ExtraProfileIn],
    extra_glasses: List[ExtraGlassIn],
    extra_remotes: Optional[List[ExtraRemoteIn]] = None,
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # Malzemeler
    for extra in extras:
        obj = ProjectExtraMaterial(
            id=uuid4(),
            project_id=project.id,
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm,
        )
        _apply_pdf(obj, getattr(extra, "pdf", None))
        db.add(obj)

    # Profiller
    for profile in extra_profiles:
        obj = ProjectExtraProfile(
            id=uuid4(),
            project_id=project.id,
            profile_id=profile.profile_id,
            cut_length_mm=profile.cut_length_mm,
            cut_count=profile.cut_count,
        )
        _apply_pdf(obj, getattr(profile, "pdf", None))
        db.add(obj)

    # Camlar
    for glass in extra_glasses:
        area_m2 = (glass.width_mm / 1000) * (glass.height_mm / 1000)
        obj = ProjectExtraGlass(
            id=uuid4(),
            project_id=project.id,
            glass_type_id=glass.glass_type_id,
            width_mm=glass.width_mm,
            height_mm=glass.height_mm,
            count=glass.count,
            area_m2=area_m2,
        )
        _apply_pdf(obj, getattr(glass, "pdf", None))
        db.add(obj)

    # Kumandalar (extra)
    for r in extra_remotes or []:
        unit_price = r.unit_price
        if unit_price is None:
            rem = db.query(Remote).filter(Remote.id == r.remote_id).first()
            unit_price = float(rem.price) if rem and rem.price is not None else None

        obj = ProjectExtraRemote(
            id=uuid4(),
            project_id=project.id,
            remote_id=r.remote_id,
            count=r.count,
            unit_price=unit_price,
        )
        _apply_pdf(obj, getattr(r, "pdf", None))
        db.add(obj)

    db.commit()
    db.refresh(project)
    return project


def get_project_requirements_detailed(
    db: Session,
    project_id: UUID
) -> ProjectRequirementsDetailedOut:
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
        variant = db.query(SystemVariant).filter(SystemVariant.id == ps.system_variant_id).first()
        system = db.query(System).filter(System.id == variant.system_id).first()

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
                order_index=p.order_index,
                profile=db.query(Profile).filter(Profile.id == p.profile_id).first(),
                pdf=_pdf_from_obj(p),
            )
            for p in profiles_raw
        ]

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
                order_index=g.order_index,
                glass_type=db.query(GlassType).filter(GlassType.id == g.glass_type_id).first(),
                pdf=_pdf_from_obj(g),
            )
            for g in glasses_raw
        ]

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
                type=m.type,                           # ✅ yeni
                piece_length_mm=m.piece_length_mm,     # ✅ yeni
                order_index=m.order_index,
                material=db.query(OtherMaterial).filter(OtherMaterial.id == m.material_id).first(),
                pdf=_pdf_from_obj(m),
            )
            for m in materials_raw
        ]

        remotes_raw = (
            db.query(ProjectSystemRemote)
            .filter(ProjectSystemRemote.project_system_id == ps.id)
            .all()
        )
        remotes = []
        for r in remotes_raw:
            remote_obj = db.query(Remote).filter(Remote.id == r.remote_id).first()
            remotes.append(
                RemoteInProjectOut(
                    remote_id=r.remote_id,
                    count=r.count,
                    order_index=r.order_index,
                    unit_price=float(r.unit_price) if r.unit_price is not None else None,
                    remote=remote_obj,
                    pdf=_pdf_from_obj(r),
                )
            )

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
                materials=materials,
                remotes=remotes,
            )
        )

    extras_raw = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.project_id == project_id).all()
    extra_requirements = [
        MaterialInProjectOut(
            material_id=e.material_id,
            cut_length_mm=e.cut_length_mm,
            count=e.count,
            material=db.query(OtherMaterial).filter(OtherMaterial.id == e.material_id).first(),
            pdf=_pdf_from_obj(e),
        )
        for e in extras_raw
    ]

    # ekstra profiller (detaylı)
    extra_profiles = []
    for p in db.query(ProjectExtraProfile).filter(ProjectExtraProfile.project_id == project_id).all():
        prof = db.query(Profile).filter(Profile.id == p.profile_id).first()
        extra_profiles.append(
            ExtraProfileDetailed(
                profile_id=p.profile_id,
                cut_length_mm=float(p.cut_length_mm),
                cut_count=p.cut_count,
                profile=prof,
                pdf=_pdf_from_obj(p),
            )
        )

    # ekstra camlar (detaylı)
    extra_glasses = []
    for g in db.query(ProjectExtraGlass).filter(ProjectExtraGlass.project_id == project_id).all():
        gt = db.query(GlassType).filter(GlassType.id == g.glass_type_id).first()
        extra_glasses.append(
            ExtraGlassDetailed(
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                glass_type=gt,
                pdf=_pdf_from_obj(g),
            )
        )

    # ekstra kumandalar (detaylı)
    extra_remotes = []
    for r in db.query(ProjectExtraRemote).filter(ProjectExtraRemote.project_id == project_id).all():
        remote_obj = db.query(Remote).filter(Remote.id == r.remote_id).first()
        extra_remotes.append(
            ExtraRemoteDetailed(
                remote_id=r.remote_id,
                count=r.count,
                unit_price=float(r.unit_price) if r.unit_price is not None else None,
                remote=remote_obj,
                pdf=_pdf_from_obj(r),
            )
        )

    return ProjectRequirementsDetailedOut(
        id=project.id,
        customer=customer,
        profile_color=project.profile_color,
        glass_color=project.glass_color,
        systems=result_systems,
        extra_requirements=extra_requirements,
        extra_profiles=extra_profiles,
        extra_glasses=extra_glasses,
        extra_remotes=extra_remotes,
    )

# ------------------------------------------------------------
# Renk güncelleme
# ------------------------------------------------------------

def update_project_colors(
    db: Session,
    project_id: UUID,
    profile_color_id: Optional[UUID],
    glass_color_id: Optional[UUID]
) -> Optional[Project]:
    project = get_project(db, project_id)
    if not project:
        return None
    project.profile_color_id = profile_color_id
    project.glass_color_id = glass_color_id
    db.commit()
    db.refresh(project)
    return project

# ------------------------------------------------------------
# Extra Profile CRUD
# ------------------------------------------------------------

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
        cut_count=cut_count,
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    extra.pdf = _pdf_from_obj(extra)
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
    extra.pdf = _pdf_from_obj(extra)
    return extra


def delete_project_extra_profile(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraProfile).filter(ProjectExtraProfile.id == extra_id).delete()
    db.commit()
    return bool(deleted)

# ------------------------------------------------------------
# Extra Glass CRUD
# ------------------------------------------------------------

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
        area_m2=area_m2,
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    extra.pdf = _pdf_from_obj(extra)
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
    extra.pdf = _pdf_from_obj(extra)
    return extra


def delete_project_extra_glass(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraGlass).filter(ProjectExtraGlass.id == extra_id).delete()
    db.commit()
    return bool(deleted)

# ------------------------------------------------------------
# Extra Material CRUD
# ------------------------------------------------------------

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
        cut_length_mm=cut_length_mm,
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    extra.pdf = _pdf_from_obj(extra)
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
    extra.pdf = _pdf_from_obj(extra)
    return extra


def delete_project_extra_material(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.id == extra_id).delete()
    db.commit()
    return bool(deleted)

# ------------------------------------------------------------
# Extra Remote CRUD
# ------------------------------------------------------------
def create_project_extra_remote(
    db: Session,
    project_id: UUID,
    remote_id: UUID,
    count: int,
    unit_price: Optional[float] = None,
) -> ProjectExtraRemote:
    extra = ProjectExtraRemote(
        id=uuid4(),
        project_id=project_id,
        remote_id=remote_id,
        count=count,
        unit_price=unit_price,
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    extra.pdf = _pdf_from_obj(extra)
    return extra


def update_project_extra_remote(
    db: Session,
    extra_id: UUID,
    count: Optional[int] = None,
    unit_price: Optional[float] = None,
) -> Optional[ProjectExtraRemote]:
    extra = db.query(ProjectExtraRemote).filter(ProjectExtraRemote.id == extra_id).first()
    if not extra:
        return None
    if count is not None:
        extra.count = count
    if unit_price is not None:
        extra.unit_price = unit_price
    db.commit()
    db.refresh(extra)
    extra.pdf = _pdf_from_obj(extra)
    return extra


def delete_project_extra_remote(
    db: Session,
    extra_id: UUID
) -> bool:
    deleted = db.query(ProjectExtraRemote).filter(ProjectExtraRemote.id == extra_id).delete()
    db.commit()
    return bool(deleted)


def list_project_extra_remotes(db: Session, project_id: UUID) -> List[ProjectExtraRemote]:
    return (
        db.query(ProjectExtraRemote)
          .filter(ProjectExtraRemote.project_id == project_id)
          .all()
    )

# ------------------------------------------------------------
# Listeler
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# ProjectSystem güncelle/sil
# ------------------------------------------------------------

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
        return None  # 🔧 önce None kontrolü

    variant_id = ps.system_variant_id

    tpl_profiles = {
        t.profile_id: t.order_index
        for t in db.query(SystemProfileTemplate)
                   .filter_by(system_variant_id=variant_id)
                   .all()
    }
    tpl_glasses = {
        t.glass_type_id: t.order_index
        for t in db.query(SystemGlassTemplate)
                   .filter_by(system_variant_id=variant_id)
                   .all()
    }
    tpl_materials = {
        t.material_id: t
        for t in db.query(SystemMaterialTemplate)
                .filter_by(system_variant_id=variant_id)
                .all()
    }

    tpl_remotes = {
        t.remote_id: t.order_index
        for t in db.query(SystemRemoteTemplate)
                   .filter_by(system_variant_id=variant_id)
                   .all()
    }

    # Temel alanlar
    ps.width_mm  = payload.width_mm
    ps.height_mm = payload.height_mm
    ps.quantity  = payload.quantity

    # Önce mevcut child kayıtları sil
    db.query(ProjectSystemProfile).filter(ProjectSystemProfile.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemGlass).filter(ProjectSystemGlass.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemMaterial).filter(ProjectSystemMaterial.project_system_id == project_system_id).delete(synchronize_session=False)
    db.query(ProjectSystemRemote).filter(ProjectSystemRemote.project_system_id == project_system_id).delete(synchronize_session=False)  # 🆕

    # Yeniden ekle
    for p in payload.profiles:
        obj = ProjectSystemProfile(
            id=uuid4(),
            project_system_id=ps.id,
            profile_id=p.profile_id,
            cut_length_mm=p.cut_length_mm,
            cut_count=p.cut_count,
            total_weight_kg=p.total_weight_kg,
            order_index=tpl_profiles.get(p.profile_id),
        )
        _apply_pdf(obj, getattr(p, "pdf", None))
        db.add(obj)

    for g in payload.glasses:
        obj = ProjectSystemGlass(
            id=uuid4(),
            project_system_id=ps.id,
            glass_type_id=g.glass_type_id,
            width_mm=g.width_mm,
            height_mm=g.height_mm,
            count=g.count,
            area_m2=g.area_m2,
            order_index=tpl_glasses.get(g.glass_type_id),
        )
        _apply_pdf(obj, getattr(g, "pdf", None))
        db.add(obj)

    for m in payload.materials:
        tpl = tpl_materials.get(m.material_id)
        typ = m.type if m.type is not None else (tpl.type if tpl else None)
        piece_len = m.piece_length_mm if m.piece_length_mm is not None else (tpl.piece_length_mm if tpl else None)

        obj = ProjectSystemMaterial(
            id=uuid4(),
            project_system_id=ps.id,
            material_id=m.material_id,
            cut_length_mm=m.cut_length_mm,
            count=m.count,
            type=typ,                       # ✅
            piece_length_mm=piece_len,      # ✅
            order_index=(tpl.order_index if tpl else None),
        )
        _apply_pdf(obj, getattr(m, "pdf", None))
        db.add(obj)

    # Kumandalar
    for r in getattr(payload, "remotes", []) or []:
        unit_price = r.unit_price
        if unit_price is None:
            rem = db.query(Remote).filter(Remote.id == r.remote_id).first()
            unit_price = float(rem.price) if rem and rem.price is not None else None

        obj = ProjectSystemRemote(
            id=uuid4(),
            project_system_id=ps.id,
            remote_id=r.remote_id,
            count=r.count,
            unit_price=unit_price,
            order_index=tpl_remotes.get(r.remote_id),
        )
        _apply_pdf(obj, getattr(r, "pdf", None))
        db.add(obj)

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
    db.query(ProjectSystemRemote).filter(ProjectSystemRemote.project_system_id == project_system_id).delete(synchronize_session=False)  # 🆕

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
