from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.color import ColorCreate, ColorUpdate, ColorOut
from app.crud.color import (
    create_color,
    get_colors,
    get_color,
    update_color,
    delete_color
)

router = APIRouter(prefix="/api/colors", tags=["Colors"])


@router.post("/", response_model=ColorOut, status_code=201)
def create_color_endpoint(payload: ColorCreate, db: Session = Depends(get_db)):
    return create_color(db, payload)


@router.get("/", response_model=list[ColorOut])
def list_colors(type: str | None = Query(default=None, regex="^(profile|glass)$"), db: Session = Depends(get_db)):
    """
    Renkleri listeler. `?type=profile` veya `?type=glass` ile filtrelenebilir.
    """
    return get_colors(db, type_filter=type)


@router.get("/{color_id}", response_model=ColorOut)
def get_color_endpoint(color_id: UUID, db: Session = Depends(get_db)):
    color = get_color(db, color_id)
    if not color:
        raise HTTPException(404, detail="Color not found")
    return color


@router.put("/{color_id}", response_model=ColorOut)
def update_color_endpoint(color_id: UUID, payload: ColorUpdate, db: Session = Depends(get_db)):
    updated = update_color(db, color_id, payload)
    if not updated:
        raise HTTPException(404, detail="Color not found")
    return updated


@router.delete("/{color_id}", status_code=204)
def delete_color_endpoint(color_id: UUID, db: Session = Depends(get_db)):
    if not delete_color(db, color_id):
        raise HTTPException(404, detail="Color not found")
    return
