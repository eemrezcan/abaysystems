from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.app_user import AppUser
from app.schemas.calculation_helper import CalculationHelperOut, CalculationHelperUpdate
from app.crud import calculation_helper as crud

router = APIRouter(prefix="/api/me/calculation-helpers", tags=["me-calculation-helpers"])


@router.get("", response_model=CalculationHelperOut)
def get_my_helper(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    if current_user.role == "admin":
        obj = crud.get_by_owner(db, None)
        return crud.serialize_out(obj, is_default=True, has_record=bool(obj))

    obj, is_default, has_record = crud.resolve_for_owner(db, current_user.id)
    return crud.serialize_out(obj, is_default=is_default, has_record=has_record)


@router.put("", response_model=CalculationHelperOut)
def upsert_my_helper(
    payload: CalculationHelperUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Admin: varsayılan kaydı owner_id=None olarak günceller
    if current_user.role == "admin":
        obj = crud.upsert(
            db,
            owner_id=None,
            bicak_payi=payload.bicak_payi,
            boya_payi=payload.boya_payi,
        )
        return crud.serialize_out(obj, is_default=True, has_record=True)

    # Dealer: kendi kaydını owner_id=user.id ile günceller
    obj = crud.upsert(
        db,
        owner_id=current_user.id,
        bicak_payi=payload.bicak_payi,
        boya_payi=payload.boya_payi,
    )
    return crud.serialize_out(obj, is_default=False, has_record=True)
