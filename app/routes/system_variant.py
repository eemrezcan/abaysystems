# app/routes/system_variant.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.crud.system_variant import (
    create_system_variant,
    get_system_variants,
    get_system_variant,
    update_system_variant,
    delete_system_variant,
    get_variants_for_system
)
from app.schemas.system import (
    SystemVariantCreate,
    SystemVariantUpdate,
    SystemVariantOut
)

router = APIRouter(prefix="/api/system-variants", tags=["SystemVariants"])

@router.post("/", response_model=SystemVariantOut, status_code=201)
def create_variant(
    payload: SystemVariantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new SystemVariant for a given System.
    """
    return create_system_variant(db, payload)

@router.get("/", response_model=list[SystemVariantOut])
def list_variants(db: Session = Depends(get_db)):
    """
    List all SystemVariants.
    """
    return get_system_variants(db)

#@router.get("/{variant_id}", response_model=SystemVariantOut)
#def get_variant_endpoint(
#    variant_id: UUID,
#    db: Session = Depends(get_db)
#):
#    """
#    Retrieve a specific SystemVariant by ID.
#    """
#    obj = get_system_variant(db, variant_id)
#    if not obj:
#        raise HTTPException(status_code=404, detail="SystemVariant not found")
#    return obj

@router.put("/{variant_id}", response_model=SystemVariantOut)
def update_variant(
    variant_id: UUID,
    payload: SystemVariantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update fields of an existing SystemVariant.
    """
    obj = update_system_variant(db, variant_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return obj

@router.delete("/{variant_id}", status_code=204)
def delete_variant(
    variant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a SystemVariant by ID.
    """
    deleted = delete_system_variant(db, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SystemVariant not found")
    return

# ----- New: Variants by System -----
@router.get(
    "/system/{system_id}",
    response_model=list[SystemVariantOut],
    summary="List all SystemVariants for a given System ID"
)
def list_variants_by_system(
    system_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all variants for the specified system.
    """
    variants = get_variants_for_system(db, system_id)
    return variants
