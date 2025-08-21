# app/models/app_user.py
import uuid
from sqlalchemy import Column, String, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class AppUser(Base):
    __tablename__ = "app_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username      = Column(String(50), unique=True, nullable=True)
    password_hash = Column(String(200), nullable=True)
    role = Column(String(20), nullable=False, default="dealer")
    # --- Dealer bilgileri ---
    name        = Column(String(100), nullable=True)   # Bayi/Firma adı
    email       = Column(String(200), unique=True, nullable=True)
    phone       = Column(String(20),  nullable=True)
    owner_name  = Column(String(100), nullable=True)
    city        = Column(String(100), nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)

    # Yeni alanlar:
    status            = Column(String(20), nullable=False, default="invited")  # invited | active | suspended
    password_set_at   = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('invited','active','suspended')",
            name="ck_app_user_status",
        ),
    )



    # İsterseniz ilişki tanımları:
    orders    = relationship("SalesOrder", back_populates="creator")
    customers = relationship(
    "Customer",
    back_populates="customer_user",
    primaryjoin="AppUser.id == foreign(Customer.dealer_id)",
)
    projects = relationship(
        "Project",
        back_populates="creator",
        primaryjoin="AppUser.id == foreign(Project.created_by)",
    )