# app/routes/me_project_code.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser

from app.schemas.project_code_rule import (
    ProjectCodeRuleCreate, ProjectCodeRuleUpdate, ProjectCodeRuleOut, NextProjectCodeOut
)
from app.crud import project_code as crud_pc

router = APIRouter(prefix="/api/me/project-code", tags=["me-project-code"])

# app/routes/me_project_code.py — get_my_rule (TAMAMINI BU HALİYLE DEĞİŞTİR)

@router.get("/rule", response_model=ProjectCodeRuleOut)
def get_my_rule(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Varsayılan "PROFORMA-1" kuralını otomatik sağla
    rule = crud_pc.get_or_create_default_rule(db, current_user.id)
    return rule


@router.post("/rule", response_model=ProjectCodeRuleOut, status_code=201)
def create_my_rule(
    payload: ProjectCodeRuleCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    if crud_pc.get_rule_by_owner(db, current_user.id):
        raise HTTPException(status_code=409, detail="Bu hesap için kural zaten var.")
    try:
        return crud_pc.create_rule(
            db,
            owner_id=current_user.id,
            prefix=payload.prefix,
            separator=payload.separator,
            start_number=payload.start_number,  # ⬅️ padding yok
        )
    except IntegrityError:
        db.rollback()
        # prefix global-unique değil; yine de diğer hatalar için:
        raise HTTPException(status_code=409, detail="Kural oluşturulurken bir hata oluştu.")

@router.put("/rule", response_model=ProjectCodeRuleOut)
def update_my_rule(
    payload: ProjectCodeRuleUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    rule = crud_pc.get_rule_by_owner(db, current_user.id)
    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı.")

    try:
        return crud_pc.update_rule(
            db, rule,
            prefix=payload.prefix,
            separator=payload.separator,
            start_number=payload.start_number,
            reset_sequence=(payload.reset_sequence or False),   # ✅ eklendi
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Kural güncellenirken bir hata oluştu.")
    
@router.get("/next", response_model=NextProjectCodeOut)
def preview_next_code(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    try:
        n, code = crud_pc.preview_next_code(db, current_user.id)
        return {"next_number": n, "next_code": code}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
