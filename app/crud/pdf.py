# app/crud/pdf.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.pdf import PdfTitleTemplate, PdfBrand

# ---------- Titles ----------
def titles_list(db: Session, owner_id: UUID, q: Optional[str] = None) -> List[PdfTitleTemplate]:
    qry = db.query(PdfTitleTemplate).filter(
        PdfTitleTemplate.owner_id == owner_id,
        PdfTitleTemplate.is_deleted == False  # noqa: E712
    )
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(PdfTitleTemplate.key.ilike(like)))
    return qry.order_by(PdfTitleTemplate.created_at.desc()).all()

def title_get(db: Session, owner_id: UUID, id: UUID) -> Optional[PdfTitleTemplate]:
    return (
        db.query(PdfTitleTemplate)
          .filter(PdfTitleTemplate.id == id,
                  PdfTitleTemplate.owner_id == owner_id,
                  PdfTitleTemplate.is_deleted == False)  # noqa: E712
          .first()
    )

def title_get_by_key(db: Session, owner_id: UUID, key: str) -> Optional[PdfTitleTemplate]:
    return (
        db.query(PdfTitleTemplate)
          .filter(PdfTitleTemplate.key == key,
                  PdfTitleTemplate.owner_id == owner_id,
                  PdfTitleTemplate.is_deleted == False)  # noqa: E712
          .first()
    )

def title_create(db: Session, owner_id: UUID, key: str, config_json: dict) -> PdfTitleTemplate:
    obj = PdfTitleTemplate(owner_id=owner_id, key=key, config_json=config_json)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def title_update(db: Session, obj: PdfTitleTemplate, *, key: Optional[str]=None, config_json: Optional[dict]=None) -> PdfTitleTemplate:
    if key is not None: obj.key = key
    if config_json is not None: obj.config_json = config_json
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def title_soft_delete(db: Session, obj: PdfTitleTemplate) -> None:
    obj.is_deleted = True
    db.add(obj); db.commit()

# ---------- Brands ----------
def brands_list(db: Session, owner_id: UUID, q: Optional[str] = None) -> List[PdfBrand]:
    qry = db.query(PdfBrand).filter(
        PdfBrand.owner_id == owner_id,
        PdfBrand.is_deleted == False  # noqa: E712
    )
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(PdfBrand.key.ilike(like)))
    return qry.order_by(PdfBrand.created_at.desc()).all()

def brand_get(db: Session, owner_id: UUID, id: UUID) -> Optional[PdfBrand]:
    return (
        db.query(PdfBrand)
          .filter(PdfBrand.id == id,
                  PdfBrand.owner_id == owner_id,
                  PdfBrand.is_deleted == False)  # noqa: E712
          .first()
    )

def brand_get_by_key(db: Session, owner_id: UUID, key: str) -> Optional[PdfBrand]:
    return (
        db.query(PdfBrand)
          .filter(PdfBrand.key == key,
                  PdfBrand.owner_id == owner_id,
                  PdfBrand.is_deleted == False)  # noqa: E712
          .first()
    )

def brand_create(db: Session, owner_id: UUID, key: str, config_json: dict) -> PdfBrand:
    obj = PdfBrand(owner_id=owner_id, key=key, config_json=config_json)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_update(db: Session, obj: PdfBrand, *, key: Optional[str]=None, config_json: Optional[dict]=None) -> PdfBrand:
    if key is not None: obj.key = key
    if config_json is not None: obj.config_json = config_json
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_set_logo(db: Session, obj: PdfBrand, logo_url: str) -> PdfBrand:
    obj.logo_url = logo_url
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def brand_soft_delete(db: Session, obj: PdfBrand) -> None:
    obj.is_deleted = True
    db.add(obj); db.commit()

def brand_clear_logo(db: Session, obj: PdfBrand) -> PdfBrand:
    obj.logo_url = None
    db.add(obj); db.commit(); db.refresh(obj)
    return obj
