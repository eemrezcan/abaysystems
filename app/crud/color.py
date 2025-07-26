from sqlalchemy.orm import Session
from uuid import UUID, uuid4

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
