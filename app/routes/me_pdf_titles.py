# app/routes/me_pdf_titles.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser
from app.schemas.pdf import PdfTitleTemplateCreate, PdfTitleTemplateUpdate, PdfTitleTemplateOut
from app.crud import pdf as crud

router = APIRouter(prefix="/api/me/pdf/titles", tags=["me-pdf-titles"])

@router.get("", response_model=List[PdfTitleTemplateOut])
def list_my_titles(q: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    # Lazy default: eksikse ekle
    crud.titles_ensure_defaults(db, current_user.id)
    return crud.titles_list(db, owner_id=current_user.id, q=q)

@router.get("/{id}", response_model=PdfTitleTemplateOut)
def get_my_title(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.title_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Title bulunamadı")
    return obj

@router.get("/by-key/{key}", response_model=PdfTitleTemplateOut)
def get_my_title_by_key(key: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    # Lazy default: çağıranlar doğrudan by-key kullanıyorsa da eksikler tamam olsun
    crud.titles_ensure_defaults(db, current_user.id)
    obj = crud.title_get_by_key(db, current_user.id, key)
    if not obj:
        raise HTTPException(status_code=404, detail="Title bulunamadı")
    return obj

@router.post("", response_model=PdfTitleTemplateOut, status_code=201)
def create_my_title(payload: PdfTitleTemplateCreate, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    if crud.title_get_by_key(db, current_user.id, payload.key):
        raise HTTPException(status_code=409, detail="Bu key ile title zaten var")
    return crud.title_create(db, owner_id=current_user.id, key=payload.key, config_json=payload.config_json)

@router.put("/{id}", response_model=PdfTitleTemplateOut)
def update_my_title(id: UUID, payload: PdfTitleTemplateUpdate, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.title_get(db, current_user.id, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Title bulunamadı")
    if payload.key and payload.key != obj.key:
        if crud.title_get_by_key(db, current_user.id, payload.key):
            raise HTTPException(status_code=409, detail="Bu key ile başka bir title var")
    return crud.title_update(db, obj, key=payload.key, config_json=payload.config_json)

@router.delete("/{id}", status_code=204)
def delete_my_title(id: UUID, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    obj = crud.title_get(db, current_user.id, id)
    if not obj:
        return
    crud.title_delete(db, obj)   # HARD DELETE
    return

@router.post("/ensure-defaults", response_model=List[str])
def ensure_defaults_now(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    """
    Varsayılan title şablonlarını şimdi yükler.
    Yanıt: Eklenen key listesi (boş ise zaten yüklü demektir).
    """
    created = crud.titles_ensure_defaults_verbose(db, current_user.id)
    return created
