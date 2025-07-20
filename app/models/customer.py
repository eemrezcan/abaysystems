# app/models/customer.py

import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class Customer(Base):
    __tablename__ = "customer"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id  = Column(
        UUID(as_uuid=True),
        ForeignKey("app_user.id", ondelete="CASCADE"),
        nullable=False
    )
    name       = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=True)
    phone      = Column(String(20), nullable=True)
    city       = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # app_user.py içindeki customers = relationship("Customer", back_populates="customer_user")
    customer_user = relationship("AppUser", back_populates="customers")

    # SalesOrder.customer ile back_populates="orders" uyumlu olacak
    orders = relationship("SalesOrder", back_populates="customer", cascade="all, delete-orphan")
