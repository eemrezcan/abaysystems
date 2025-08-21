from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db

# 🔐 roller
from app.core.security import get_current_user
from app.api.deps import get_current_admin
from app.models.app_user import AppUser

# 🔎 bayi GET filtreleri için model
from app.models.color import Color

from app.schemas.color import ColorCreate, ColorUpdate, ColorOut
from app.crud.color import (
    create_color,
    get_colors,
    get_color,
    update_color,
    delete_color,
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

@router.get("/", response_model=list[ColorOut])
def list_colors(
    type: str | None = Query(default=None, pattern="^(profile|glass)$"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Renkleri listeler. `?type=profile` veya `?type=glass` ile filtrelenebilir.
    Bayi: sadece `is_active=true AND is_deleted=false` kayıtlar döner.
    Admin: CRUD katmanındaki liste (genelde tüm silinmemiş) döner.
    """
    if current_user.role == "admin":
        return get_colors(db, type_filter=type)

    # bayi → aktif & silinmemiş
    q = db.query(Color).filter(Color.is_deleted == False, Color.is_active == True)
    if type:
        q = q.filter(Color.type == type)
    return q.order_by(Color.name.asc()).all()


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
