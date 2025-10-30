from uuid import uuid4, UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm import joinedload
from sqlalchemy import asc
from typing import Optional, List, Tuple, Any

from app.models.system import System, SystemVariant
from app.models.system_profile_template import SystemProfileTemplate
from app.models.system_glass_template import SystemGlassTemplate
from app.models.system_material_template import SystemMaterialTemplate
from app.models.system_remote_template import SystemRemoteTemplate
from app.schemas.system import (
    SystemCreate,
    SystemUpdate,
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemProfileTemplateCreate,
    SystemProfileTemplateUpdate,
    SystemGlassTemplateCreate,
    SystemGlassTemplateUpdate,
    SystemMaterialTemplateCreate,
    SystemMaterialTemplateUpdate,
    SystemFullCreate,
    SystemVariantCreateWithTemplates,
    SystemVariantUpdateWithTemplates,
    SystemRemoteTemplateCreate,
    SystemRemoteTemplateUpdate,
    RemoteTemplateIn,
)

# --- PDF helpers: request -> kolonlar, kolonlar -> response(pdf) ---
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
    if pdf_model_or_dict is None:
        return
    if hasattr(pdf_model_or_dict, "dict"):
        pdf_data = pdf_model_or_dict.dict(exclude_unset=True)
    elif isinstance(pdf_model_or_dict, dict):
        pdf_data = pdf_model_or_dict
    else:
        return
    for key, val in pdf_data.items():
        col = PDF_MAP_IN.get(key)
        if col is not None and val is not None:
            setattr(obj, col, bool(val))

def _attach_pdf(obj: Any) -> Any:
    """OUT tarafında Pydantic'in görebileceği şekilde obj.pdf alanını set eder."""
    try:
        obj.pdf = {
            "camCiktisi":                  bool(getattr(obj, "cam_ciktisi")),
            "profilAksesuarCiktisi":      bool(getattr(obj, "profil_aksesuar_ciktisi")),
            "boyaCiktisi":                bool(getattr(obj, "boya_ciktisi")),
            "siparisCiktisi":             bool(getattr(obj, "siparis_ciktisi")),
            "optimizasyonDetayliCiktisi": bool(getattr(obj, "optimizasyon_detayli_ciktisi")),
            "optimizasyonDetaysizCiktisi":bool(getattr(obj, "optimizasyon_detaysiz_ciktisi")),
        }
    except Exception:
        pass
    return obj

def _attach_pdf_many(seq):
    for o in seq:
        _attach_pdf(o)
    return seq

# ————— System CRUD —————

def create_system(db: Session, payload: SystemCreate) -> System:
    data = payload.dict(exclude_unset=True)  # is_active, sort_index dahil gelebilir
    obj = System(id=uuid4(), **data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_systems(db: Session) -> list[System]:
    return (
        db.query(System)
        .filter(System.is_deleted == False)
        .order_by(asc(System.sort_index), asc(System.name), asc(System.created_at))
        .all()
    )

def get_systems_page(
    db: Session,
    is_admin: bool,
    q: Optional[str],
    limit: Optional[int],
    offset: int,
    only_active: Optional[bool] = None,  # ✅ eklendi
) -> Tuple[List[System], int]:
    base_q = db.query(System).filter(System.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(System.is_published == True)

    if only_active is True:
        base_q = base_q.filter(System.is_active == True)  # ✅ aktif filtre

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(System.name.ilike(like))

    total = base_q.order_by(None).count()

    q_items = base_q.order_by(asc(System.sort_index), asc(System.name), asc(System.created_at))
    if limit is None:
        items = q_items.all()
    else:
        items = q_items.offset(offset).limit(limit).all()

    return items, total



def get_system(db: Session, system_id: UUID) -> System | None:
    return db.query(System).filter_by(id=system_id).first()


def update_system(db: Session, system_id: UUID, payload: SystemUpdate) -> System | None:
    obj = get_system(db, system_id)
    if not obj:
        return None
    data = payload.dict(exclude_unset=True)  # sort_index dahil gelebilir
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj



def delete_system(db: Session, system_id: UUID) -> bool:
    deleted = db.query(System).filter_by(id=system_id).delete()
    db.commit()
    return bool(deleted)

# ————— SystemVariant CRUD —————

def create_system_variant(db: Session, system_id: UUID, payload: SystemVariantCreate) -> SystemVariant:
    data = payload.dict(by_alias=True, exclude={"system_id"}, exclude_unset=True)  # is_active, sort_index gelebilir
    obj = SystemVariant(
        id=uuid4(),
        system_id=system_id,
        **data
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_system_variants(db: Session) -> list[SystemVariant]:
    return (
        db.query(SystemVariant)
        .filter(SystemVariant.is_deleted == False)
        .order_by(asc(SystemVariant.sort_index), asc(SystemVariant.name), asc(SystemVariant.created_at))
        .all()
    )


def get_system_variant(db: Session, variant_id: UUID) -> SystemVariant | None:
    return db.query(SystemVariant).filter_by(id=variant_id).first()


def update_system_variant(db: Session, variant_id: UUID, payload: SystemVariantUpdate) -> SystemVariant | None:
    obj = get_system_variant(db, variant_id)
    if not obj:
        return None
    for k, v in payload.dict(exclude_unset=True, by_alias=True).items():  # sort_index dahil
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_system_variant(db: Session, variant_id: UUID) -> bool:
    deleted = db.query(SystemVariant).filter_by(id=variant_id).delete()
    db.commit()
    return bool(deleted)

# ————— Template CRUD —————

def create_profile_template(db: Session, payload: SystemProfileTemplateCreate) -> SystemProfileTemplate:
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    obj = SystemProfileTemplate(id=uuid4(), **data)
    _apply_pdf(obj, pdf)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)

def get_profile_templates(db: Session, variant_id: UUID) -> list[SystemProfileTemplate]:
    items = (
        db.query(SystemProfileTemplate)
        .filter_by(system_variant_id=variant_id)
        .order_by(
            SystemProfileTemplate.order_index.asc().nulls_last(),
            SystemProfileTemplate.created_at.asc(),
        )

        .all()
    )
    return _attach_pdf_many(items)

def update_profile_template(db: Session, template_id: UUID, payload: SystemProfileTemplateUpdate) -> SystemProfileTemplate | None:
    obj = db.query(SystemProfileTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    for k, v in data.items():
        setattr(obj, k, v)
    _apply_pdf(obj, pdf)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)



def delete_profile_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemProfileTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)


def create_glass_template(db: Session, payload: SystemGlassTemplateCreate) -> SystemGlassTemplate:
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    obj = SystemGlassTemplate(id=uuid4(), **data)
    _apply_pdf(obj, pdf)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)

def get_glass_templates(db: Session, variant_id: UUID) -> list[SystemGlassTemplate]:
    items = (
        db.query(SystemGlassTemplate)
        .filter_by(system_variant_id=variant_id)
        .order_by(
            SystemGlassTemplate.order_index.asc().nulls_last(),
            SystemGlassTemplate.created_at.asc(),
        )

        .all()
    )
    return _attach_pdf_many(items)

def update_glass_template(db: Session, template_id: UUID, payload: SystemGlassTemplateUpdate) -> SystemGlassTemplate | None:
    obj = db.query(SystemGlassTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    for k, v in data.items():
        setattr(obj, k, v)
    _apply_pdf(obj, pdf)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)


def delete_glass_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemGlassTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)


def create_material_template(db: Session, payload: SystemMaterialTemplateCreate) -> SystemMaterialTemplate:
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    obj = SystemMaterialTemplate(id=uuid4(), **data)
    _apply_pdf(obj, pdf)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)

def get_material_templates(db: Session, variant_id: UUID) -> list[SystemMaterialTemplate]:
    items = (
        db.query(SystemMaterialTemplate)
        .filter_by(system_variant_id=variant_id)
        .order_by(
            SystemMaterialTemplate.order_index.asc().nulls_last(),
            SystemMaterialTemplate.created_at.asc(),
        )

        .all()
    )
    return _attach_pdf_many(items)

def update_material_template(db: Session, template_id: UUID, payload: SystemMaterialTemplateUpdate) -> SystemMaterialTemplate | None:
    obj = db.query(SystemMaterialTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    for k, v in data.items():
        setattr(obj, k, v)
    _apply_pdf(obj, pdf)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)



def delete_material_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemMaterialTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)

# ----- REMOTE TEMPLATE CRUD -----

def create_remote_template(db: Session, payload: SystemRemoteTemplateCreate) -> SystemRemoteTemplate:
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    obj = SystemRemoteTemplate(id=uuid4(), **data)
    _apply_pdf(obj, pdf)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)

def get_remote_templates(db: Session, variant_id: UUID) -> list[SystemRemoteTemplate]:
    items = (
        db.query(SystemRemoteTemplate)
        .options(joinedload(SystemRemoteTemplate.remote))
        .filter_by(system_variant_id=variant_id)
        .order_by(
            SystemRemoteTemplate.order_index.asc().nulls_last(),
            SystemRemoteTemplate.created_at.asc(),
        )

        .all()
    )
    return _attach_pdf_many(items)

def update_remote_template(db: Session, template_id: UUID, payload: SystemRemoteTemplateUpdate) -> SystemRemoteTemplate | None:
    obj = db.query(SystemRemoteTemplate).filter_by(id=template_id).first()
    if not obj:
        return None
    data = payload.dict(exclude_unset=True)
    pdf = data.pop("pdf", None)
    for k, v in data.items():
        setattr(obj, k, v)
    _apply_pdf(obj, pdf)
    db.commit()
    db.refresh(obj)
    return _attach_pdf(obj)


def delete_remote_template(db: Session, template_id: UUID) -> bool:
    deleted = db.query(SystemRemoteTemplate).filter_by(id=template_id).delete()
    db.commit()
    return bool(deleted)


# ————— Combined template fetch —————

def get_system_templates(db: Session, variant_id: UUID):
    profiles = (
        db.query(SystemProfileTemplate)
        .options(joinedload(SystemProfileTemplate.profile))
        .filter(SystemProfileTemplate.system_variant_id == variant_id)
        .order_by(
            asc(SystemProfileTemplate.order_index).nulls_last(),
            asc(SystemProfileTemplate.created_at),
        )
        .all()
    )
    _attach_pdf_many(profiles)

    glasses = (
        db.query(SystemGlassTemplate)
        .options(joinedload(SystemGlassTemplate.glass_type))
        .filter(SystemGlassTemplate.system_variant_id == variant_id)
        .order_by(
            asc(SystemGlassTemplate.order_index).nulls_last(),
            asc(SystemGlassTemplate.created_at),
        )
        .all()
    )
    _attach_pdf_many(glasses)

    materials = (
        db.query(SystemMaterialTemplate)
        .options(joinedload(SystemMaterialTemplate.material))
        .filter(SystemMaterialTemplate.system_variant_id == variant_id)
        .order_by(
            asc(SystemMaterialTemplate.order_index).nulls_last(),
            asc(SystemMaterialTemplate.created_at),
        )
        .all()
    )
    _attach_pdf_many(materials)

    remotes = (
        db.query(SystemRemoteTemplate)
        .options(joinedload(SystemRemoteTemplate.remote))
        .filter(SystemRemoteTemplate.system_variant_id == variant_id)
        .order_by(
            asc(SystemRemoteTemplate.order_index).nulls_last(),
            asc(SystemRemoteTemplate.created_at),
        )
        .all()
    )
    _attach_pdf_many(remotes)

    return profiles, glasses, materials, remotes



# ————— Combined full creation —————

def create_system_full(db: Session, payload: SystemFullCreate):
    # 1) System
    system = System(
        id=uuid4(),
        name=payload.name,
        description=payload.description,
        photo_url=payload.photo_url,
        is_active=(payload.is_active if payload.is_active is not None else True),  # ✅
        sort_index=(payload.sort_index if payload.sort_index is not None else 0),  # ✅
    )
    db.add(system)
    db.flush()

    # 2) Variant
    variant_data = payload.variant.dict(by_alias=True, exclude_unset=True)
    variant = SystemVariant(
        id=uuid4(),
        system_id=system.id,
        name=variant_data["name"],
        photo_url=variant_data.get("photo_url"),
        is_active=(variant_data.get("is_active", True)),  # ✅
        sort_index=(variant_data.get("sort_index", 0)),   # ✅
    )
    db.add(variant)
    db.flush()

    # 3) Glass templates
    for g in payload.glass_configs or []:
        tpl = SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            glass_type_id=g.glass_type_id,
            formula_width=g.formula_width,
            formula_height=g.formula_height,
            formula_count=g.formula_count
        )
        db.add(tpl)

    db.commit()
    db.refresh(system)
    return {
        "system": system,
        "variant": variant,
        "glass_templates": payload.glass_configs
    }


def get_system_variant_detail(db: Session, variant_id: UUID) -> Optional[SystemVariant]:
    variant = (
        db.query(SystemVariant)
        .filter(SystemVariant.id == variant_id)
        .options(
            joinedload(SystemVariant.system),
            joinedload(SystemVariant.profile_templates).joinedload(SystemProfileTemplate.profile),
            joinedload(SystemVariant.glass_templates).joinedload(SystemGlassTemplate.glass_type),
            joinedload(SystemVariant.material_templates).joinedload(SystemMaterialTemplate.material),
            joinedload(SystemVariant.remote_templates).joinedload(SystemRemoteTemplate.remote)
        )
        .first()
    )
    if variant:
        _attach_pdf_many(variant.profile_templates)
        _attach_pdf_many(variant.glass_templates)
        _attach_pdf_many(variant.material_templates)
        _attach_pdf_many(variant.remote_templates)
    return variant



def create_system_variant_with_templates(db: Session, payload: SystemVariantCreateWithTemplates) -> SystemVariant:
    # 1) Variant
    variant = SystemVariant(
        id=uuid4(),
        system_id=payload.system_id,
        name=payload.name,
        is_active=(payload.is_active if payload.is_active is not None else True),  # ✅
        sort_index=(payload.sort_index if payload.sort_index is not None else 0),  # ✅
    )
    db.add(variant)
    db.flush()

    # 2) Profile şablonları
    for i, pt in enumerate(payload.profile_templates):
        obj = SystemProfileTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            profile_id=pt.profile_id,
            formula_cut_length=pt.formula_cut_length,
            formula_cut_count=pt.formula_cut_count,
            order_index=pt.order_index if pt.order_index is not None else i,
            is_painted=bool(getattr(pt, "is_painted", False)),
        )
        _apply_pdf(obj, getattr(pt, "pdf", None))
        db.add(obj)

    # 3) Glass şablonları
    for i, gt in enumerate(payload.glass_templates):
        obj = SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            glass_type_id=gt.glass_type_id,
            formula_width=gt.formula_width,
            formula_height=gt.formula_height,
            formula_count=gt.formula_count,
            order_index=gt.order_index if gt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(gt, "pdf", None))
        db.add(obj)

    # 4) Material şablonları
    for i, mt in enumerate(payload.material_templates):
        obj = SystemMaterialTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            material_id=mt.material_id,
            formula_quantity=mt.formula_quantity,
            formula_cut_length=mt.formula_cut_length,
            unit_price=mt.unit_price,
            type=mt.type,
            piece_length_mm=mt.piece_length_mm,
            order_index=mt.order_index if mt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(mt, "pdf", None))
        db.add(obj)

    # 4.5) Remote şablonları
    for i, rt in enumerate(payload.remote_templates):
        obj = SystemRemoteTemplate(
            id=uuid4(),
            system_variant_id=variant.id,
            remote_id=rt.remote_id,
            order_index=rt.order_index if rt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(rt, "pdf", None))
        db.add(obj)

    db.commit()
    db.refresh(variant)
    return variant



# ————— Update SystemVariant + all its templates —————
def update_system_variant_with_templates(db: Session, variant_id: UUID, payload: SystemVariantUpdateWithTemplates) -> SystemVariant:
    variant = get_system_variant(db, variant_id)
    if not variant:
        raise ValueError("Variant not found")

    if payload.name is not None:
        variant.name = payload.name
    if payload.is_active is not None:   # ✅ is_active güncelle
        variant.is_active = bool(payload.is_active)
    if payload.sort_index is not None:  # ✅ sıralama güncelle
        variant.sort_index = int(payload.sort_index)

    # Eski şablonları temizle
    db.query(SystemProfileTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.query(SystemGlassTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.query(SystemMaterialTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.query(SystemRemoteTemplate).filter_by(system_variant_id=variant_id).delete(synchronize_session=False)
    db.flush()

    # PROFIL
    for i, pt in enumerate(payload.profile_templates):
        obj = SystemProfileTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            profile_id=pt.profile_id,
            formula_cut_length=pt.formula_cut_length,
            formula_cut_count=pt.formula_cut_count,
            order_index=pt.order_index if pt.order_index is not None else i,
            is_painted=bool(getattr(pt, "is_painted", False)),
        )
        _apply_pdf(obj, getattr(pt, "pdf", None))
        db.add(obj)

    # CAM
    for i, gt in enumerate(payload.glass_templates):
        obj = SystemGlassTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            glass_type_id=gt.glass_type_id,
            formula_width=gt.formula_width,
            formula_height=gt.formula_height,
            formula_count=gt.formula_count,
            order_index=gt.order_index if gt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(gt, "pdf", None))
        db.add(obj)

    # MALZEME
    for i, mt in enumerate(payload.material_templates):
        obj = SystemMaterialTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            material_id=mt.material_id,
            formula_quantity=mt.formula_quantity,
            formula_cut_length=mt.formula_cut_length,
            unit_price=mt.unit_price,
            type=mt.type,
            piece_length_mm=mt.piece_length_mm,
            order_index=mt.order_index if mt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(mt, "pdf", None))
        db.add(obj)

    # REMOTE
    for i, rt in enumerate(payload.remote_templates):
        obj = SystemRemoteTemplate(
            id=uuid4(),
            system_variant_id=variant_id,
            remote_id=rt.remote_id,
            order_index=rt.order_index if rt.order_index is not None else i
        )
        _apply_pdf(obj, getattr(rt, "pdf", None))
        db.add(obj)

    db.commit()
    db.refresh(variant)
    return variant