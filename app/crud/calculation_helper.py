from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.calculation_helper import CalculationHelper
from app.schemas.calculation_helper import CalculationHelperOut


def get_by_owner(db: Session, owner_id: Optional[UUID]) -> Optional[CalculationHelper]:
    return (
        db.query(CalculationHelper)
        .filter(CalculationHelper.owner_id == owner_id)
        .first()
    )


def upsert(db: Session, *, owner_id: Optional[UUID], bicak_payi: float, boya_payi: float) -> CalculationHelper:
    obj = get_by_owner(db, owner_id)
    if obj is None:
        obj = CalculationHelper(owner_id=owner_id)

    obj.bicak_payi = bicak_payi
    obj.boya_payi = boya_payi

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def resolve_for_owner(db: Session, owner_id: UUID) -> Tuple[Optional[CalculationHelper], bool, bool]:
    """
    Döner: (record or None, is_default, has_record)
    has_record: veritabanında gerçek kayıt var mı (owner veya default)
    """
    own = get_by_owner(db, owner_id)
    if own:
        return own, False, True

    default_obj = get_by_owner(db, None)
    if default_obj:
        return default_obj, True, True

    return None, True, False


def serialize_out(obj: Optional[CalculationHelper], *, is_default: bool, has_record: bool) -> CalculationHelperOut:
    if obj is not None:
        return CalculationHelperOut(
            id=getattr(obj, "id", None),
            owner_id=getattr(obj, "owner_id", None),
            bicak_payi=float(obj.bicak_payi) if obj.bicak_payi is not None else 0.0,
            boya_payi=float(obj.boya_payi) if obj.boya_payi is not None else 0.0,
            is_default=is_default,
            has_record=has_record,
        )

    # Kayıt yoksa 0 döner
    return CalculationHelperOut(
        id=None,
        owner_id=None,
        bicak_payi=0.0,
        boya_payi=0.0,
        is_default=is_default,
        has_record=has_record,
    )
