from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.crud.customer import (
    create_customer,
    get_customer,
    get_customers_by_dealer,
    update_customer,
    delete_customer
)
from app.core.security import get_current_user
from app.models.app_user import AppUser

router = APIRouter(prefix="/api/customers", tags=["Customers"])

@router.post("/", response_model=CustomerOut, status_code=201)
def create_customer_endpoint(
    payload: CustomerCreate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Yeni müşteri oluşturur. dealer_id otomatik current_user.id olarak set edilir.
    """
    return create_customer(db, dealer_id=current_user.id, payload=payload)

@router.get("/", response_model=List[CustomerOut])
def list_customers_endpoint(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Oturum açan kullanıcının tüm aktif müşterilerini listeler.
    """
    return get_customers_by_dealer(db, dealer_id=current_user.id)

@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer_endpoint(
    customer_id: UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli müşteriyi döner.
    """
    cust = get_customer(db, customer_id)
    if not cust or cust.dealer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust

@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer_endpoint(
    customer_id: UUID,
    payload: CustomerUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mevcut müşteriyi günceller.
    """
    cust = get_customer(db, customer_id)
    if not cust or cust.dealer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Customer not found")
    updated = update_customer(db, customer_id, payload)
    return updated

@router.delete("/{customer_id}", status_code=204)
def delete_customer_endpoint(
    customer_id: UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Müşteriyi soft-delete yapar.
    """
    cust = get_customer(db, customer_id)
    if not cust or cust.dealer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Customer not found")
    success = delete_customer(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return
