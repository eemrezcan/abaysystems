# app/routes/order.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.order import (
    get_sales_order,
    get_sales_orders,
    get_sales_orders_by_customer,
    create_sales_order,
    update_sales_order_status,
)
from app.schemas.order import (
    SalesOrderCreate,
    SalesOrderOut,
    SalesOrderUpdate,
)
from app.db.session import get_db

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.get("/", response_model=List[SalesOrderOut])
def read_sales_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_sales_orders(db, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=SalesOrderOut)
def read_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    order = get_sales_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/customer/{customer_id}", response_model=List[SalesOrderOut])
def read_sales_orders_by_customer(
    customer_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_sales_orders_by_customer(db, customer_id=customer_id, skip=skip, limit=limit)


@router.post("/", response_model=SalesOrderOut, status_code=201)
def create_order(
    order_in: SalesOrderCreate,
    db: Session = Depends(get_db),
):
    return create_sales_order(db, order_in)


@router.patch("/{order_id}/status", response_model=SalesOrderOut)
def update_order_status(
    order_id: UUID,
    status_update: SalesOrderUpdate,
    db: Session = Depends(get_db),
):
    if status_update.status is None:
        raise HTTPException(status_code=400, detail="Status field is required")
    order = update_sales_order_status(db, order_id, status_update.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
