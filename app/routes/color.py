from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from typing import Optional  

from math import ceil 

from app.db.session import get_db

# 🔐 roller
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 bayi GET filtreleri için model
from app.models.color import Color

from app.schemas.color import ColorCreate, ColorUpdate, ColorOut, ColorPageOut 
from app.crud.color import (
    create_color,
    get_colors,
    get_color,
    update_color,
    delete_color,
    get_colors_page
)

router = APIRouter(prefix="/api/colors", tags=["Colors"])


# ----------------- ADMIN-ONLY (CREATE/UPDATE/DELETE) -----------------

@router.post("/", response_model=ColorOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_color_endpoint(payload: ColorCreate, db: Session = Depends(get_db)):
    return create_color(db, payload)


@router.put("/{color_id}", response_model=ColorOut, dependencies=[Depends(get_current_admin)])
def update_color_endpoint(color_id: UUID, payload: ColorUpdate, db: Session = Depends(get_db)):
    updated = update_color(db, color_id, payload)
    if not updated:
        raise HTTPException(404, detail="Color not found")
    return updated


@router.delete("/{color_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_color_endpoint(color_id: UUID, db: Session = Depends(get_db)):
    if not delete_color(db, color_id):
        raise HTTPException(404, detail="Color not found")
    return


# ----------------- GET (BAYİ + ADMIN) -----------------

@router.get("/", response_model=ColorPageOut)
def list_colors(
    type: str | None = Query(default=None, pattern="^(profile|glass)$", description="Renk tipi filtresi"),
    q: str | None = Query(default=None, description="Ada göre filtre (contains, case-insensitive)"),
    limit: int = Query(default=50, ge=1, le=200, description="Sayfa başına kayıt (page size)"),
    page: int = Query(default=1, ge=1, description="1'den başlayan sayfa numarası"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Renkleri listeler. Bayi: sadece aktif & silinmemiş. Admin: silinmemiş tüm renkler.
    Paginated döner: items, total, page, limit, total_pages, has_next, has_prev
    """
    is_admin = (current_user.role == "admin")
    offset = (page - 1) * limit

    items, total = get_colors_page(
        db=db,
        is_admin=is_admin,
        type_filter=type,
        q=q,
        limit=limit,
        offset=offset,
    )

    total_pages = ceil(total / limit) if total > 0 else 0
    return ColorPageOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=(page < total_pages) if total_pages > 0 else False,
        has_prev=(page > 1) and (total_pages > 0),
    )



@router.get("/{color_id}", response_model=ColorOut)
def get_color_endpoint(
    color_id: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    color = get_color(db, color_id)
    if not color:
        raise HTTPException(404, detail="Color not found")

    # bayi pasif/silinmiş rengi göremesin
    if current_user.role != "admin" and (color.is_deleted or not color.is_active):
        raise HTTPException(404, detail="Color not found")

    return color
