# app/models/order.py
import uuid
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.app_user import AppUser
from app.models.customer import Customer
from app.db.base import Base

class SalesOrder(Base):
    __tablename__ = "sales_order"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), unique=True, nullable=False)
    order_date = Column(Date, nullable=False)
    order_name = Column(String(100), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id"), nullable=False)
    status = Column(String(30), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    creator = relationship("AppUser", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="orders")

class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("sales_order.id", ondelete="CASCADE"), nullable=False)
    project_system_id = Column(UUID(as_uuid=True), ForeignKey("project_system.id"), nullable=False)
    color = Column(String(50), nullable=True)
    width_mm = Column(Numeric, nullable=False)
    height_mm = Column(Numeric, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("SalesOrder", back_populates="items")
    profiles = relationship("OrderItemProfile", back_populates="order_item", cascade="all, delete-orphan")
    glasses = relationship("OrderItemGlass", back_populates="order_item", cascade="all, delete-orphan")
    materials = relationship("OrderItemMaterial", back_populates="order_item", cascade="all, delete-orphan")
    extra_materials = relationship("OrderItemExtraMaterial", back_populates="order_item", cascade="all, delete-orphan")


class OrderItemProfile(Base):
    __tablename__ = "order_item_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_item.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profile.id"), nullable=False)
    cut_length_mm = Column(Numeric, nullable=False)
    cut_count = Column(Integer, nullable=False)
    total_weight_kg = Column(Numeric, nullable=True)

    order_item = relationship("OrderItem", back_populates="profiles")


class OrderItemGlass(Base):
    __tablename__ = "order_item_glass"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_item.id", ondelete="CASCADE"), nullable=False)
    glass_type_id = Column(UUID(as_uuid=True), ForeignKey("glass_type.id"), nullable=False)
    width_mm = Column(Numeric, nullable=False)
    height_mm = Column(Numeric, nullable=False)
    count = Column(Integer, nullable=False)
    area_m2 = Column(Numeric, nullable=True)

    order_item = relationship("OrderItem", back_populates="glasses")


class OrderItemMaterial(Base):
    __tablename__ = "order_item_material"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_item.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    cut_length_mm = Column(Numeric, nullable=True)
    count = Column(Integer, nullable=False)

    order_item = relationship("OrderItem", back_populates="materials")


class OrderItemExtraMaterial(Base):
    __tablename__ = "order_item_extra_material"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_item.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    cut_length_mm = Column(Numeric, nullable=True)
    count = Column(Integer, nullable=False)

    order_item = relationship("OrderItem", back_populates="extra_materials")
