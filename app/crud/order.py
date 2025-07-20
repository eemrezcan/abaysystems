# app/crud/order.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.order import (
    SalesOrder,
    OrderItem,
    OrderItemProfile,
    OrderItemGlass,
    OrderItemMaterial,
    OrderItemExtraMaterial,
)
from app.schemas.order import SalesOrderCreate


def get_sales_order(db: Session, order_id: UUID) -> Optional[SalesOrder]:
    return db.query(SalesOrder).filter(SalesOrder.id == order_id).first()


def get_sales_orders(
    db: Session, skip: int = 0, limit: int = 100
) -> List[SalesOrder]:
    return db.query(SalesOrder).offset(skip).limit(limit).all()


def get_sales_orders_by_customer(
    db: Session, customer_id: UUID, skip: int = 0, limit: int = 100
) -> List[SalesOrder]:
    return (
        db.query(SalesOrder)
        .filter(SalesOrder.customer_id == customer_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_sales_order(db: Session, order: SalesOrderCreate) -> SalesOrder:
    db_order = SalesOrder(
        order_no=order.order_no,
        order_date=order.order_date,
        order_name=order.order_name,
        project_id=order.project_id,
        customer_id=order.customer_id,
        status=order.status,
        created_by=order.created_by,
    )
    db.add(db_order)
    db.flush()

    for item in order.items:
        db_item = OrderItem(
            order_id=db_order.id,
            project_system_id=item.project_system_id,
            color=item.color,
            width_mm=item.width_mm,
            height_mm=item.height_mm,
            quantity=item.quantity,
        )
        db.add(db_item)
        db.flush()

        for profile in item.profiles:
            db_profile = OrderItemProfile(
                order_item_id=db_item.id,
                profile_id=profile.profile_id,
                cut_length_mm=profile.cut_length_mm,
                cut_count=profile.cut_count,
                total_weight_kg=profile.total_weight_kg,
            )
            db.add(db_profile)

        for glass in item.glasses:
            db_glass = OrderItemGlass(
                order_item_id=db_item.id,
                glass_type_id=glass.glass_type_id,
                width_mm=glass.width_mm,
                height_mm=glass.height_mm,
                count=glass.count,
                area_m2=glass.area_m2,
            )
            db.add(db_glass)

        for material in item.materials:
            db_material = OrderItemMaterial(
                order_item_id=db_item.id,
                material_id=material.material_id,
                cut_length_mm=material.cut_length_mm,
                count=material.count,
            )
            db.add(db_material)

        for extra in item.extra_materials:
            db_extra = OrderItemExtraMaterial(
                order_item_id=db_item.id,
                material_id=extra.material_id,
                cut_length_mm=extra.cut_length_mm,
                count=extra.count,
            )
            db.add(db_extra)

    db.commit()
    db.refresh(db_order)
    return db_order


def update_sales_order_status(
    db: Session, order_id: UUID, new_status: str
) -> Optional[SalesOrder]:
    db_order = get_sales_order(db, order_id)
    if not db_order:
        return None
    db_order.status = new_status
    db.commit()
    db.refresh(db_order)
    return db_order
