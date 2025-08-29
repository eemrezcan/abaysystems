# app/crud/customer.py

from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from typing import Optional, List, Tuple

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from typing import Optional

from sqlalchemy import func

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


def get_customers(
    db: Session,
    owner_id: UUID,
    name: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,  # 🟢 yeni
) -> list[Customer]:
    """
    Kendi müşterilerini döndürür:
    - Sadece is_deleted=False
    - En yeni -> en eski (created_at DESC)
    - İsteğe bağlı 'name' filtresi (case-insensitive contains)
    - 'offset' ve 'limit' ile sayfalama
    """
    q = (
        db.query(Customer)
        .filter(
            Customer.dealer_id == owner_id,
            Customer.is_deleted == False,
        )
        .order_by(Customer.created_at.desc())
    )

    if name:
        like_val = f"%{name.lower()}%"
        q = q.filter(func.lower(Customer.company_name).like(like_val))

    if offset:
        q = q.offset(offset)  # 🟢 yeni

    if limit is not None:
        q = q.limit(limit)

    return q.all()

def get_customers_page(
    db: Session,
    owner_id: UUID,
    name: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Customer], int]:
    """
    Filtrelenmiş toplam kayıt sayısı + sayfadaki kayıtları birlikte döndürür.
    Sadece is_deleted=False olanlar.
    """
    base_q = (
        db.query(Customer)
        .filter(
            Customer.dealer_id == owner_id,
            Customer.is_deleted == False,
        )
    )

    if name:
        like_val = f"%{name.lower()}%"
        base_q = base_q.filter(func.lower(Customer.company_name).like(like_val))

    total = base_q.order_by(None).count()

    items = (
        base_q.order_by(Customer.created_at.desc())
              .offset(offset)
              .limit(limit)
              .all()
    )
    return items, total


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
