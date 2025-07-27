# app/crud/customer.py

from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from typing import Optional, List

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


def create_customer(
    db: Session,
    dealer_id: UUID,
    payload: CustomerCreate
) -> Customer:
    """
    Yeni müşteri oluşturur ve döner.
    """
    customer = Customer(
        id=uuid4(),
        dealer_id=dealer_id,
        company_name=payload.company_name,
        name=payload.name,
        phone=payload.phone,
        city=payload.city
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(
    db: Session,
    customer_id: UUID
) -> Optional[Customer]:
    """
    ID ve is_deleted=False koşuluyla tek müşteri döner.
    """
    return (
        db.query(Customer)
          .filter(
              Customer.id == customer_id,
              Customer.is_deleted == False
          )
          .first()
    )


def get_customers_by_dealer(
    db: Session,
    dealer_id: UUID
) -> List[Customer]:
    """
    Belirli bayiye ait tüm aktif müşterileri listeler.
    """
    return (
        db.query(Customer)
          .filter(
              Customer.dealer_id == dealer_id,
              Customer.is_deleted == False
          )
          .all()
    )


def update_customer(
    db: Session,
    customer_id: UUID,
    payload: CustomerUpdate
) -> Optional[Customer]:
    """
    Müşterinin alanlarını günceller.
    """
    customer = get_customer(db, customer_id)
    if not customer:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(
    db: Session,
    customer_id: UUID
) -> bool:
    """
    is_deleted flag'ini True yapar (soft delete).
    """
    customer = get_customer(db, customer_id)
    if not customer:
        return False
    customer.is_deleted = True
    db.commit()
    return True
