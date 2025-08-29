from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from typing import Optional, List, Tuple

from app.models.color import Color
from app.schemas.color import ColorCreate, ColorUpdate


def create_color(db: Session, payload: ColorCreate) -> Color:
    color = Color(
        id=uuid4(),
        name=payload.name,
        type=payload.type,
        unit_cost=payload.unit_cost
    )
    db.add(color)
    db.commit()
    db.refresh(color)
    return color


def get_colors(db: Session, type_filter: str | None = None) -> list[Color]:
    query = db.query(Color)
    if type_filter:
        query = query.filter(Color.type == type_filter)
    return query.order_by(Color.name).all()

def get_colors_page(
    db: Session,
    is_admin: bool,
    type_filter: Optional[str],
    q: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Color], int]:
    """
    Renkleri sayfalı döndürür.
    - Her zaman is_deleted = False
    - Admin değilse ayrıca is_active = True
    - type_filter verilirse (profile|glass) filtrelenir
    - q verilirse name ILIKE '%q%' filtrelenir
    """
    base_q = db.query(Color).filter(Color.is_deleted == False)

    if not is_admin:
        base_q = base_q.filter(Color.is_active == True)

    if type_filter:
        base_q = base_q.filter(Color.type == type_filter)

    if q:
        like = f"%{q}%"
        base_q = base_q.filter(Color.name.ilike(like))

    total = base_q.order_by(None).count()

    items = (
        base_q.order_by(Color.name.asc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total

def get_color(db: Session, color_id: UUID) -> Color | None:
    return db.query(Color).filter(Color.id == color_id).first()


def update_color(db: Session, color_id: UUID, payload: ColorUpdate) -> Color | None:
    color = get_color(db, color_id)
    if not color:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(color, field, value)
    db.commit()
    db.refresh(color)
    return color


def delete_color(db: Session, color_id: UUID) -> bool:
    deleted = db.query(Color).filter(Color.id == color_id).delete()
    db.commit()
    return bool(deleted)
