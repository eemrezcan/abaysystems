# app/crud/project.py

from uuid import uuid4
from datetime import datetime, date
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
from sqlalchemy.exc import IntegrityError
from app.models.color import Color


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
    today = datetime.utcnow()

    project = Project(
        id=uuid4(),
        customer_id=payload.customer_id,
        project_name=payload.project_name,
        created_by=created_by,
        project_kodu=code,
        created_at=datetime.utcnow(),
        press_price=payload.press_price,
        painted_price=payload.painted_price,

        # 🆕 Yeni alanlar
        is_teklif=True if payload.is_teklif is None else bool(payload.is_teklif),
        paint_status="durum belirtilmedi",
        glass_status="durum belirtilmedi",
        production_status="durum belirtilmedi",
        approval_date=today,  # 🆕 kural: yeni proje oluşur oluşmaz bugünün tarihi
    )
    db.add(project)

    # 3) Tek commit (unique çakışmasına karşı bir retry)
    try:
        db.commit()
    except IntegrityError:
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
    offset: int = 0,
    is_teklif: Optional[bool] = None,   # 🆕
    # --- yeni filtreler ---
    paint_status: Optional[str] = None,
    glass_status: Optional[str] = None,
    production_status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
) -> list[Project]:
    """
    Kendi projelerini döndürür.
    Ek filtreler:
      - paint_status / glass_status / production_status: exact match
      - customer_id: eşleşen müşteri
    Sıralama:
      - is_teklif=True   → created_at DESC
      - is_teklif=False  → approval_date DESC, created_at DESC
      - is_teklif=None   → created_at DESC
    """
    query = db.query(Project).filter(Project.created_by == owner_id)

    # Arama
    if name:
        like_val = f"%{name.lower()}%"
        query = query.filter(func.lower(Project.project_name).like(like_val))

    # Filtreler
    if is_teklif is not None:
        query = query.filter(Project.is_teklif == bool(is_teklif))
    if paint_status:
        query = query.filter(Project.paint_status == paint_status.strip())
    if glass_status:
        query = query.filter(Project.glass_status == glass_status.strip())
    if production_status:
        query = query.filter(Project.production_status == production_status.strip())
    if customer_id:
        query = query.filter(Project.customer_id == customer_id)

    # Sıralama
    if is_teklif is False:
        query = query.order_by(Project.approval_date.desc(), Project.created_at.desc())
    else:
        query = query.order_by(Project.created_at.desc())

    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    return query.all()



def get_projects_page(
    db: Session,
    owner_id: UUID,
    name: Optional[str],
    code: Optional[str],
    limit: int,
    offset: int,
    is_teklif: Optional[bool] = None,   # 🆕
    # --- yeni filtreler ---
    paint_status: Optional[str] = None,
    glass_status: Optional[str] = None,
    production_status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
) -> Tuple[List[Project], int]:
    """
    Filtrelenmiş toplam kayıt sayısı + sayfadaki kayıtlar.
    - name: project_name contains (CI)
    - code: project_kodu contains (CI)
    - is_teklif: True/False'a göre filtre ve sıralama
    - paint_status / glass_status / production_status: exact match
    - customer_id: eşleşen müşteri
    """
    base_q = db.query(Project).filter(Project.created_by == owner_id)

    # Metin aramaları
    if name:
        like_val = f"%{name.lower()}%"
        base_q = base_q.filter(func.lower(Project.project_name).like(like_val))
    if code:
        code_like = f"%{code.lower()}%"
        base_q = base_q.filter(func.lower(Project.project_kodu).like(code_like))

    # Durum + müşteri filtreleri
    if is_teklif is not None:
        base_q = base_q.filter(Project.is_teklif == bool(is_teklif))
    if paint_status:
        base_q = base_q.filter(Project.paint_status == paint_status.strip())
    if glass_status:
        base_q = base_q.filter(Project.glass_status == glass_status.strip())
    if production_status:
        base_q = base_q.filter(Project.production_status == production_status.strip())
    if customer_id:
        base_q = base_q.filter(Project.customer_id == customer_id)

    # Toplam
    total = base_q.order_by(None).count()

    # Sıralama
    if is_teklif is False:
        order_clause = [Project.approval_date.desc(), Project.created_at.desc()]
    else:
        order_clause = [Project.created_at.desc()]

    # Sayfa
    items = (
        base_q.order_by(*order_clause)
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

    # is_teklif toggle kuralı (önce mevcut değeri hatırla)
    before_is_teklif = getattr(proj, "is_teklif", True)

    data = payload.dict(exclude_unset=True)

    # created_at açıkça gönderildiyse güncelle
    if "created_at" in data:
        proj.created_at = data["created_at"]

    # Basit alanlar
    if "customer_id" in data:
        proj.customer_id = data["customer_id"]
    if "project_name" in data:
        proj.project_name = data["project_name"]
    if "profile_color_id" in data:
        proj.profile_color_id = data["profile_color_id"]
    if "glass_color_id" in data:
        proj.glass_color_id = data["glass_color_id"]
    if "press_price" in data:
        proj.press_price = data["press_price"]
    if "painted_price" in data:
        proj.painted_price = data["painted_price"]

    # 🆕 Status alanları
    if "paint_status" in data and data["paint_status"] is not None:
        proj.paint_status = data["paint_status"]
    if "glass_status" in data and data["glass_status"] is not None:
        proj.glass_status = data["glass_status"]
    if "production_status" in data and data["production_status"] is not None:
        proj.production_status = data["production_status"]

    # 🆕 is_teklif değişimi
    if "is_teklif" in data and data["is_teklif"] is not None:
        new_is_teklif = bool(data["is_teklif"])
        if before_is_teklif is True and new_is_teklif is False:
            # True → False: approval_date “o anın tarihi”ne çekilir
            proj.approval_date = datetime.utcnow()
        # False → True: approval_date DEĞİŞMEZ
        proj.is_teklif = new_is_teklif

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

    # ✅ Global benzersizlik kontrolü (aynı kod başka projede var mı?)
    exists = (
        db.query(Project)
        .filter(Project.project_kodu == new_code, Project.id != project_id)
        .first()
    )
    if exists:
        # kontrollü uyarı → route 400'e çeviriyor
        raise ValueError("Bu proje kodu (prefix+numara) zaten kullanılıyor.")

    proj.project_kodu = new_code

    # ✅ Ek güvenlik: muhtemel yarış/DB düzeyinde unique ihlallerinde 500 yerine 400 üretelim
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Bu proje kodu (prefix+numara) zaten kullanılıyor.")

    db.refresh(proj)
    return proj

def update_project_all(
    db: Session,
    project_id: UUID,
    payload: ProjectUpdate,
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

    # Müşteri sahiplik kontrolü (varsa)
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

    # Proje kodu numarası güncellemesi (varsa)
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

    # Alanları uygula
    data = payload.dict(exclude_unset=True)
    data.pop("project_kodu", None)

    if "created_at" in data:
        proj.created_at = data["created_at"]
    if "project_name" in data:
        proj.project_name = data["project_name"]
    if "customer_id" in data:
        proj.customer_id = data["customer_id"]
    if "profile_color_id" in data:
        proj.profile_color_id = data["profile_color_id"]
    if "glass_color_id" in data:
        proj.glass_color_id = data["glass_color_id"]
    if "press_price" in data:
        proj.press_price = data["press_price"]
    if "painted_price" in data:
        proj.painted_price = data["painted_price"]

    # 🆕 Status alanları
    if "paint_status" in data and data["paint_status"] is not None:
        proj.paint_status = data["paint_status"]
    if "glass_status" in data and data["glass_status"] is not None:
        proj.glass_status = data["glass_status"]
    if "production_status" in data and data["production_status"] is not None:
        proj.production_status = data["production_status"]

    # 🆕 is_teklif toggle
    if "is_teklif" in data and data["is_teklif"] is not None:
        before = bool(getattr(proj, "is_teklif", True))
        after = bool(data["is_teklif"])
        if before is True and after is False:
            proj.approval_date = datetime.utcnow()  # True → False: şimdi
        # False → True: dokunma
        proj.is_teklif = after

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
        # Şablonlara göre order_index haritaları
        tpl_profiles = {
            t.profile_id: t
            for t in db.query(SystemProfileTemplate)
                    .filter(SystemProfileTemplate.system_variant_id == sys_req.system_variant_id)
                    .all()
        }


        # ... cam ve malzeme haritaları aynı kalsın ...

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
            tpl = tpl_profiles.get(p.profile_id)
            obj = ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg,
                order_index=(tpl.order_index if tpl is not None else None),
                is_painted=bool(getattr(tpl, "is_painted", False)) if tpl is not None else False,
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

            # 💲 Fiyat snapshot önceliği: payload → template → katalog
            unit_price = getattr(m, "unit_price", None)
            if unit_price is None:
                if tpl is not None and tpl.unit_price is not None:
                    unit_price = float(tpl.unit_price)
                else:
                    mat = db.query(OtherMaterial).filter(OtherMaterial.id == m.material_id).first()
                    unit_price = float(mat.unit_price) if mat and mat.unit_price is not None else None

            obj = ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count,
                type=typ,
                piece_length_mm=piece_len,
                unit_price=unit_price,  # 💲
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

    # --- Proje seviyesi ekstra malzemeler (DÖNGÜ DIŞI)
    for extra in payload.extra_requirements:
        # 💲 payload.unit_price → katalog fallback
        unit_price = getattr(extra, "unit_price", None)
        if unit_price is None:
            mat = db.query(OtherMaterial).filter(OtherMaterial.id == extra.material_id).first()
            unit_price = float(mat.unit_price) if mat and mat.unit_price is not None else None

        obj = ProjectExtraMaterial(
            id=uuid4(),
            project_id=project.id,
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm,
            unit_price=unit_price,  # 💲
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
            t.profile_id: t
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
            tpl = tpl_profiles.get(p.profile_id)
            obj = ProjectSystemProfile(
                id=uuid4(),
                project_system_id=ps.id,
                profile_id=p.profile_id,
                cut_length_mm=p.cut_length_mm,
                cut_count=p.cut_count,
                total_weight_kg=p.total_weight_kg,
                order_index=(tpl.order_index if tpl is not None else None),
                is_painted=bool(getattr(tpl, "is_painted", False)) if tpl is not None else False,
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
            tpl = tpl_materials.get(m.material_id)

            typ = m.type if m.type is not None else (tpl.type if tpl else None)
            piece_len = m.piece_length_mm if m.piece_length_mm is not None else (tpl.piece_length_mm if tpl else None)

            # 💲 payload → template → katalog
            unit_price = getattr(m, "unit_price", None)
            if unit_price is None:
                if tpl is not None and tpl.unit_price is not None:
                    unit_price = float(tpl.unit_price)
                else:
                    mat = db.query(OtherMaterial).filter(OtherMaterial.id == m.material_id).first()
                    unit_price = float(mat.unit_price) if mat and mat.unit_price is not None else None

            obj = ProjectSystemMaterial(
                id=uuid4(),
                project_system_id=ps.id,
                material_id=m.material_id,
                cut_length_mm=m.cut_length_mm,
                count=m.count,
                type=typ,
                piece_length_mm=piece_len,
                unit_price=unit_price,  # 💲
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

    # --- Extra Materials ---
    for extra in extras:
        unit_price = getattr(extra, "unit_price", None)
        if unit_price is None:
            mat = db.query(OtherMaterial).filter(OtherMaterial.id == extra.material_id).first()
            unit_price = float(mat.unit_price) if mat and mat.unit_price is not None else None

        obj = ProjectExtraMaterial(
            id=uuid4(),
            project_id=project_id,  # 🔴 FIX: Project.id değil, parametre
            material_id=extra.material_id,
            count=extra.count,
            cut_length_mm=extra.cut_length_mm,
            unit_price=unit_price,
        )
        _apply_pdf(obj, getattr(extra, "pdf", None))
        db.add(obj)

    # --- Extra Profiles ---
    for profile in extra_profiles:
        obj = ProjectExtraProfile(
            id=uuid4(),
            project_id=project_id,  # 🔴 FIX
            profile_id=profile.profile_id,
            cut_length_mm=profile.cut_length_mm,
            cut_count=profile.cut_count,
            is_painted=bool(getattr(profile, "is_painted", False)),
            unit_price=getattr(profile, "unit_price", None),
        )
        _apply_pdf(obj, getattr(profile, "pdf", None))
        db.add(obj)

    # --- Extra Glasses ---
    for glass in extra_glasses:
        area_m2 = (glass.width_mm / 1000) * (glass.height_mm / 1000)
        obj = ProjectExtraGlass(
            id=uuid4(),
            project_id=project_id,  # 🔴 FIX
            glass_type_id=glass.glass_type_id,
            width_mm=glass.width_mm,
            height_mm=glass.height_mm,
            count=glass.count,
            area_m2=area_m2,
            unit_price=getattr(glass, "unit_price", None),
        )
        _apply_pdf(obj, getattr(glass, "pdf", None))
        db.add(obj)


    # --- Extra Remotes (opsiyonel) ---
    for r in (extra_remotes or []):
        unit_price = getattr(r, "unit_price", None)
        if unit_price is None:
            rem = db.query(Remote).filter(Remote.id == r.remote_id).first()
            unit_price = float(rem.unit_price) if rem and rem.unit_price is not None else None

        obj = ProjectExtraRemote(
            id=uuid4(),
            project_id=project_id,  # 🔴 FIX
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
                is_painted=bool(getattr(p, "is_painted", False)),
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
        glasses = []
        for g in glasses_raw:
            glass_color_obj = (
                db.query(Color).filter(Color.id == g.glass_color_id).first()
                if getattr(g, "glass_color_id", None) else None
            )
            glasses.append(
                GlassInProjectOut(
                    id=g.id,  # ✅ ProjectSystemGlass.id
                    glass_type_id=g.glass_type_id,
                    width_mm=g.width_mm,
                    height_mm=g.height_mm,
                    count=g.count,
                    area_m2=g.area_m2,
                    order_index=g.order_index,
                    glass_type=db.query(GlassType).filter(GlassType.id == g.glass_type_id).first(),
                    glass_color_id=getattr(g, "glass_color_id", None),
                    glass_color=glass_color_obj,
                    pdf=_pdf_from_obj(g),
                )
            )


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
                unit_price=float(m.unit_price) if m.unit_price is not None else None,
                type=m.type,
                piece_length_mm=m.piece_length_mm,
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

    # --- EXTRA'lar ---
    # Extra Material (DETAY + id)
    extra_materials_out = []
    for e in db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.project_id == project_id).all():
        mat = db.query(OtherMaterial).filter(OtherMaterial.id == e.material_id).first()
        extra_materials_out.append({
            "id": e.id,  # 🔴 id eklendi
            "material_id": e.material_id,
            "count": e.count,
            "cut_length_mm": e.cut_length_mm,
            "unit_price": float(e.unit_price) if e.unit_price is not None else None,
            "material": mat,
            "pdf": _pdf_from_obj(e),
        })

    # Extra Profile (DETAY + id)
    extra_profiles = []
    for p in db.query(ProjectExtraProfile).filter(ProjectExtraProfile.project_id == project_id).all():
        prof = db.query(Profile).filter(Profile.id == p.profile_id).first()
        extra_profiles.append(
            ExtraProfileDetailed(
                id=p.id,  # 🔴 id eklendi
                profile_id=p.profile_id,
                cut_length_mm=float(p.cut_length_mm),
                cut_count=p.cut_count,
                is_painted=bool(getattr(p, "is_painted", False)),
                unit_price=float(p.unit_price) if p.unit_price is not None else None,
                profile=prof,
                pdf=_pdf_from_obj(p),
            )
        )

    # Extra Glass (DETAY + id)
    extra_glasses = []
    for g in db.query(ProjectExtraGlass).filter(ProjectExtraGlass.project_id == project_id).all():
        gt = db.query(GlassType).filter(GlassType.id == g.glass_type_id).first()
        glass_color_obj = db.query(Color).filter(Color.id == g.glass_color_id).first() if getattr(g, "glass_color_id", None) else None
        extra_glasses.append(
            ExtraGlassDetailed(
                id=g.id,
                project_extra_glass_id=g.id,
                glass_type_id=g.glass_type_id,
                width_mm=float(g.width_mm),
                height_mm=float(g.height_mm),
                count=g.count,
                unit_price=float(g.unit_price) if g.unit_price is not None else None,
                glass_type=gt,
                # 🆕
                glass_color_id=getattr(g, "glass_color_id", None),
                glass_color=glass_color_obj,
                pdf=_pdf_from_obj(g),
            )
        )


    # Extra Remote (DETAY + id)
    extra_remotes = []
    for r in db.query(ProjectExtraRemote).filter(ProjectExtraRemote.project_id == project_id).all():
        remote_obj = db.query(Remote).filter(Remote.id == r.remote_id).first()
        extra_remotes.append(
            ExtraRemoteDetailed(
                id=r.id,  # 🔴 id eklendi
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
        press_price=float(project.press_price) if project.press_price is not None else None,
        painted_price=float(project.painted_price) if project.painted_price is not None else None,
        systems=result_systems,
        # ⬇️ Şemanız ExtraMaterialDetailed bekliyorsa cast etmek yerine dict döndürdük;
        # Pydantic modeliniz id + material alanlarını içeriyorsa birebir uyuşacak.
        extra_requirements=extra_materials_out,
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
# Glass color updates (system & extra)
# ------------------------------------------------------------

def update_project_system_glass_color(
    db: Session,
    project_system_glass_id: UUID,
    glass_color_id: Optional[UUID],
):
    """
    Tek bir ProjectSystemGlass satırının cam rengini günceller (None => temizler).
    """
    obj = (
        db.query(ProjectSystemGlass)
          .filter(ProjectSystemGlass.id == project_system_glass_id)
          .first()
    )
    if not obj:
        return None
    obj.glass_color_id = glass_color_id
    db.commit()
    db.refresh(obj)
    obj.pdf = _pdf_from_obj(obj)
    return obj


def bulk_update_project_system_glass_colors(
    db: Session,
    items: List[Tuple[UUID, Optional[UUID]]],
) -> int:
    """
    Birden fazla ProjectSystemGlass satırını toplu günceller.
    items: [(project_system_glass_id, glass_color_id_or_None), ...]
    Dönen değer: başarıyla güncellenen satır sayısı.
    """
    updated = 0
    for psg_id, color_id in items:
        obj = db.query(ProjectSystemGlass).filter(ProjectSystemGlass.id == psg_id).first()
        if not obj:
            continue
        obj.glass_color_id = color_id
        updated += 1
    db.commit()
    return updated


def update_project_extra_glass_color(
    db: Session,
    extra_glass_id: UUID,
    glass_color_id: Optional[UUID],
):
    """
    Tek bir ProjectExtraGlass satırının cam rengini günceller (None => temizler).
    """
    obj = (
        db.query(ProjectExtraGlass)
          .filter(ProjectExtraGlass.id == extra_glass_id)
          .first()
    )
    if not obj:
        return None
    obj.glass_color_id = glass_color_id
    db.commit()
    db.refresh(obj)
    obj.pdf = _pdf_from_obj(obj)
    return obj


def bulk_update_project_extra_glass_colors(
    db: Session,
    items: List[Tuple[UUID, Optional[UUID]]],
) -> int:
    """
    Birden fazla ProjectExtraGlass satırını toplu günceller.
    items: [(extra_glass_id, glass_color_id_or_None), ...]
    Dönen değer: başarıyla güncellenen satır sayısı.
    """
    updated = 0
    for ex_id, color_id in items:
        obj = db.query(ProjectExtraGlass).filter(ProjectExtraGlass.id == ex_id).first()
        if not obj:
            continue
        obj.glass_color_id = color_id
        updated += 1
    db.commit()
    return updated

def bulk_update_system_glass_color_by_type(
    db: Session,
    project_id: UUID,
    system_variant_id: UUID,
    glass_type_id: UUID,
    glass_color_id: Optional[UUID],
) -> int:
    """
    Verilen project_id içinde, system_variant_id + glass_type_id eşleşen TÜM ProjectSystemGlass
    kayıtlarının glass_color_id değerini günceller. Etkilenen satır sayısını döndürür.
    (JOIN'lı update yerine IN (subquery) kullanır.)
    """
    # 1) Etkilenecek satırların ID'lerini alt-sorgu ile çek
    id_subq = (
        db.query(ProjectSystemGlass.id)
          .join(ProjectSystem, ProjectSystemGlass.project_system_id == ProjectSystem.id)
          .filter(
              ProjectSystem.project_id == project_id,
              ProjectSystem.system_variant_id == system_variant_id,
              ProjectSystemGlass.glass_type_id == glass_type_id,
          )
          .subquery()
    )

    # 2) IN (subquery) ile güvenli bulk update
    updated = (
        db.query(ProjectSystemGlass)
          .filter(ProjectSystemGlass.id.in_(db.query(id_subq.c.id)))
          .update({ProjectSystemGlass.glass_color_id: glass_color_id}, synchronize_session=False)
    )

    db.commit()
    return int(updated or 0)


def bulk_update_all_glass_colors_in_project(
    db: Session,
    project_id: UUID,
    glass_color_id: Optional[UUID],
) -> dict:
    """
    Projede yer alan TÜM camların (ProjectSystemGlass + ProjectExtraGlass) rengini günceller.
    Dönüş: {"system_updated": X, "extra_updated": Y, "total": X+Y}
    """
    # System içindeki camlar → IN (subquery) yaklaşımı
    sys_ids_subq = (
        db.query(ProjectSystemGlass.id)
          .join(ProjectSystem, ProjectSystemGlass.project_system_id == ProjectSystem.id)
          .filter(ProjectSystem.project_id == project_id)
          .subquery()
    )
    sys_updated = (
        db.query(ProjectSystemGlass)
          .filter(ProjectSystemGlass.id.in_(db.query(sys_ids_subq.c.id)))
          .update({ProjectSystemGlass.glass_color_id: glass_color_id}, synchronize_session=False)
    )

    # Extra camlar → join yok, direkt update
    extra_updated = (
        db.query(ProjectExtraGlass)
          .filter(ProjectExtraGlass.project_id == project_id)
          .update({ProjectExtraGlass.glass_color_id: glass_color_id}, synchronize_session=False)
    )

    db.commit()
    return {
        "system_updated": int(sys_updated or 0),
        "extra_updated": int(extra_updated or 0),
        "total": int((sys_updated or 0) + (extra_updated or 0)),
    }



def bulk_update_glass_colors_by_type_in_project(
    db: Session,
    project_id: UUID,
    glass_type_id: UUID,
    glass_color_id: Optional[UUID],
) -> dict:
    """
    Projede, verilen glass_type_id'ye sahip TÜM camların (ProjectSystemGlass + ProjectExtraGlass)
    rengini günceller.
    Dönüş: {"system_updated": X, "extra_updated": Y, "total": X+Y}
    """
    # System içindeki camlar (type filtresiyle) → IN (subquery)
    sys_ids_subq = (
        db.query(ProjectSystemGlass.id)
          .join(ProjectSystem, ProjectSystemGlass.project_system_id == ProjectSystem.id)
          .filter(
              ProjectSystem.project_id == project_id,
              ProjectSystemGlass.glass_type_id == glass_type_id,
          )
          .subquery()
    )
    sys_updated = (
        db.query(ProjectSystemGlass)
          .filter(ProjectSystemGlass.id.in_(db.query(sys_ids_subq.c.id)))
          .update({ProjectSystemGlass.glass_color_id: glass_color_id}, synchronize_session=False)
    )

    # Extra camlar → join yok, direkt update
    extra_updated = (
        db.query(ProjectExtraGlass)
          .filter(
              ProjectExtraGlass.project_id == project_id,
              ProjectExtraGlass.glass_type_id == glass_type_id,
          )
          .update({ProjectExtraGlass.glass_color_id: glass_color_id}, synchronize_session=False)
    )

    db.commit()
    return {
        "system_updated": int(sys_updated or 0),
        "extra_updated": int(extra_updated or 0),
        "total": int((sys_updated or 0) + (extra_updated or 0)),
    }


# ------------------------------------------------------------
# Extra Profile CRUD
# ------------------------------------------------------------

def create_project_extra_profile(
    db: Session,
    project_id: UUID,
    profile_id: UUID,
    cut_length_mm: float,
    cut_count: int,
    is_painted: Optional[bool] = False,
    unit_price: Optional[float] = None,
) -> ProjectExtraProfile:
    extra = ProjectExtraProfile(
        id=uuid4(),
        project_id=project_id,
        profile_id=profile_id,
        cut_length_mm=cut_length_mm,
        cut_count=cut_count,
        is_painted=bool(is_painted),
        unit_price=unit_price,
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
    cut_count: Optional[int] = None,
    # NEW 👇
    is_painted: Optional[bool] = None,
    unit_price: Optional[float] = None,
) -> Optional[ProjectExtraProfile]:
    extra = db.query(ProjectExtraProfile).filter(ProjectExtraProfile.id == extra_id).first()
    if not extra:
        return None

    if cut_length_mm is not None:
        extra.cut_length_mm = cut_length_mm
    if cut_count is not None:
        extra.cut_count = cut_count
    # NEW 👇
    if is_painted is not None:
        extra.is_painted = bool(is_painted)

    if unit_price is not None:
        extra.unit_price = unit_price

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
    count: int,
    unit_price: Optional[float] = None,
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
        unit_price=unit_price,
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
    count: Optional[int] = None,
    unit_price: Optional[float] = None,
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
    if unit_price is not None:
        extra.unit_price = unit_price

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
    cut_length_mm: Optional[float] = None,
    unit_price: Optional[float] = None,
) -> ProjectExtraMaterial:

    extra = ProjectExtraMaterial(
        id=uuid4(),
        project_id=project_id,
        material_id=material_id,
        count=count,
        cut_length_mm=cut_length_mm,
        unit_price=unit_price,
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
    cut_length_mm: Optional[float] = None,
    unit_price: Optional[float] = None,
) -> Optional[ProjectExtraMaterial]:
    extra = db.query(ProjectExtraMaterial).filter(ProjectExtraMaterial.id == extra_id).first()
    if not extra:
        return None

    if count is not None:
        extra.count = count
    if cut_length_mm is not None:
        extra.cut_length_mm = cut_length_mm
    if unit_price is not None:
        extra.unit_price = unit_price

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
        t.profile_id: t
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
    db.query(ProjectSystemRemote).filter(ProjectSystemRemote.project_system_id == project_system_id).delete(synchronize_session=False)

    # Yeniden ekle
    for p in payload.profiles:
        tpl = tpl_profiles.get(p.profile_id)
        obj = ProjectSystemProfile(
            id=uuid4(),
            project_system_id=ps.id,
            profile_id=p.profile_id,
            cut_length_mm=p.cut_length_mm,
            cut_count=p.cut_count,
            total_weight_kg=p.total_weight_kg,
            order_index=(tpl.order_index if tpl is not None else None),
            is_painted=bool(getattr(tpl, "is_painted", False)) if tpl is not None else False,
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

        # 💲 payload → template → katalog
        unit_price = getattr(m, "unit_price", None)
        if unit_price is None:
            if tpl is not None and tpl.unit_price is not None:
                unit_price = float(tpl.unit_price)
            else:
                mat = db.query(OtherMaterial).filter(OtherMaterial.id == m.material_id).first()
                unit_price = float(mat.unit_price) if mat and mat.unit_price is not None else None

        obj = ProjectSystemMaterial(
            id=uuid4(),
            project_system_id=ps.id,
            material_id=m.material_id,
            cut_length_mm=m.cut_length_mm,
            count=m.count,
            type=typ,
            piece_length_mm=piece_len,
            unit_price=unit_price,  # 💲
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
