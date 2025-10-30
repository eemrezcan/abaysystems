# app/crud/pdf.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.pdf import PdfTitleTemplate, PdfBrand

# ------------------ DEFAULT TITLES ------------------
# ------------------ DEFAULT TITLES ------------------
DEFAULT_TITLES: List[dict] = [
    {
        "key": "pdf.optimize.detayli0",
        "config_json": {
            "theme": "default",
            "title": "Optimizasyon (Detaylı)",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "İlgili",      "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "requirements.contact_person"},
                {"label": "Renk",        "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.profile_color.name"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
    {
        "key": "pdf.optimize.detaysiz0",
        "config_json": {
            "theme": "default",
            "title": "Optimizasyon (Detaysız)",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "İlgili",      "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "requirements.contact_person"},
                {"label": "Renk",        "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.profile_color.name"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
    {
        "key": "pdf.profileAccessory0",
        "config_json": {
            "theme": "default",
            "title": "Profil Aksesuar Listesi",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "İlgili",      "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "requirements.contact_person"},
                {"label": "Renk",        "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.profile_color.name"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
    {
        "key": "pdf.paint0",
        "config_json": {
            "theme": "default",
            "title": "Boya Çıktısı",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "İlgili",      "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "requirements.contact_person"},
                {"label": "Renk",        "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.profile_color.name"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
    {
        "key": "pdf.glass0",
        "config_json": {
            "theme": "default",
            "title": "Cam Çıktısı",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": True, "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True, "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True, "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True, "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
    {
        "key": "pdf.order0",
        "config_json": {
            "theme": "default",
            "title": "Sipariş Çıktısı",
            "infoRows": [
                {"label": "Proje Adı",   "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "projectName"},
                {"label": "Müşteri",     "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.customer.name"},
                {"label": "Tarih",       "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueExpr":  "date(proje.created_at)"},
                {"label": "İlgili",      "hAlign": "left", "vAlign": "middle", "enabled": False, "labelMode": "inline", "valueField": "requirements.contact_person"},
                {"label": "Renk",        "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "requirements.profile_color.name"},
                {"label": "Proforma No", "hAlign": "left", "vAlign": "middle", "enabled": True,  "labelMode": "inline", "valueField": "proje.project_kodu"},
            ],
            "schemaVersion": 1,
            "headerBrandKey": "brand.default",
            "infoRowsLayout": {"cellPaddingX": 6, "cellPaddingY": 6, "columnsPerRow": 3},
        },
    },
]

# -------- Titles (CRUD) --------
def titles_list(db: Session, owner_id: UUID, q: Optional[str] = None) -> List[PdfTitleTemplate]:
    qry = db.query(PdfTitleTemplate).filter(PdfTitleTemplate.owner_id == owner_id)
    if q:
        like = f"%{q}%"
        # (tek alan ama or_ ile bırakıyorum, ileride genişlerse kolay)
        qry = qry.filter(or_(PdfTitleTemplate.key.ilike(like)))
    return qry.order_by(PdfTitleTemplate.created_at.desc()).all()

def title_get(db: Session, owner_id: UUID, id: UUID) -> Optional[PdfTitleTemplate]:
    return db.query(PdfTitleTemplate).filter(
        PdfTitleTemplate.id == id,
        PdfTitleTemplate.owner_id == owner_id
    ).first()

def title_get_by_key(db: Session, owner_id: UUID, key: str) -> Optional[PdfTitleTemplate]:
    return db.query(PdfTitleTemplate).filter(
        PdfTitleTemplate.key == key,
        PdfTitleTemplate.owner_id == owner_id
    ).first()

def title_create(db: Session, owner_id: UUID, key: str, config_json: dict) -> PdfTitleTemplate:
    obj = PdfTitleTemplate(owner_id=owner_id, key=key, config_json=config_json)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def title_update(db: Session, obj: PdfTitleTemplate, *, key: Optional[str]=None, config_json: Optional[dict]=None) -> PdfTitleTemplate:
    if key is not None: obj.key = key
    if config_json is not None: obj.config_json = config_json
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def title_delete(db: Session, obj: PdfTitleTemplate) -> None:
    db.delete(obj); db.commit()

def titles_ensure_defaults_verbose(db: Session, owner_id: UUID) -> list[str]:
    """
    Eksik default title'ları ekler ve eklenen key'leri döner.
    Eklenecek bir şey yoksa boş liste döner.
    """
    existing = {t.key for t in titles_list(db, owner_id)}
    created_keys: list[str] = []
    for tpl in DEFAULT_TITLES:
        if tpl["key"] not in existing:
            db.add(PdfTitleTemplate(owner_id=owner_id, key=tpl["key"], config_json=tpl["config_json"]))
            created_keys.append(tpl["key"])
    if created_keys:
        db.commit()
    return created_keys


def titles_ensure_defaults(db: Session, owner_id: UUID) -> None:
    """
    Geriye uyumlu kısa sürüm: sadece verbose fonksiyonunu çağırır.
    Dönen listeyi kullanmaz; behavior aynı kalır.
    """
    _ = titles_ensure_defaults_verbose(db, owner_id)
    return None


# ---------- Brands (tekil) ----------

DEFAULT_BRAND_KEY = "brand.default"
DEFAULT_BRAND_CONFIG = {
    "layout": "splitBrand",
    "rightBox": {
        "lines": [
            {"type": "labelValue", "label": "Adres",     "value": "Adres"},
            {"type": "labelValue", "label": "Tel",       "value": "Telefon Numarası"},
            {"type": "labelValue", "label": "WebSitesi", "value": "Web Sitesi"},
            {"type": "labelValue", "label": "mail",      "value": "mail"}
        ],
        "title": "Bayi İsmi"
    },
    "leftImage": {"type": "PNG", "width": 260, "height": 90}
}

def brand_get_single(db: Session, owner_id: UUID) -> Optional[PdfBrand]:
    return db.query(PdfBrand).filter(PdfBrand.owner_id == owner_id).first()

def brand_ensure_default(db: Session, owner_id: UUID) -> PdfBrand:
    obj = brand_get_single(db, owner_id)
    if obj:
        return obj
    obj = PdfBrand(owner_id=owner_id, key=DEFAULT_BRAND_KEY, config_json=DEFAULT_BRAND_CONFIG)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_update(db: Session, obj: PdfBrand, *, key: Optional[str]=None, config_json: Optional[dict]=None) -> PdfBrand:
    if key is not None: obj.key = key
    if config_json is not None: obj.config_json = config_json
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_delete(db: Session, obj: PdfBrand) -> None:
    db.delete(obj); db.commit()

def brand_set_logo(db: Session, obj: PdfBrand, logo_url: str) -> PdfBrand:
    obj.logo_url = logo_url
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_clear_logo(db: Session, obj: PdfBrand) -> PdfBrand:
    obj.logo_url = None
    db.add(obj); db.commit(); db.refresh(obj)
    return obj
