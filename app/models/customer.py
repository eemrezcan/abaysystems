import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey,Index, func as sa_func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Customer(Base):
    __tablename__ = "customer"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("app_user.id", ondelete="CASCADE"),
        nullable=False
    )
    company_name = Column(String(100), nullable=False)   # Firma ismi
    name = Column(String(100), nullable=False)           # Müşteri ismi
    phone = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # İlişkiler
    customer_user = relationship("AppUser", back_populates="customers")
    orders = relationship("SalesOrder", back_populates="customer", cascade="all, delete-orphan")


# 🔹 Sık filtre için birleşik index
Index("ix_customer_owner_notdeleted", Customer.dealer_id, Customer.is_deleted)

# 🔸 OPSİYONEL: Aynı bayide aynı müşteri ismini (aktif kayıtlarda) tekilleştir
#    Postgres kısmi unique index: is_deleted = false iken (dealer_id, lower(name)) benzersiz.
#    İstemezsen bu bloğu silebilirsin.
Index(
    "ux_customer_owner_name_active",
    sa_func.lower(Customer.name),
    Customer.dealer_id,
    unique=True,
    postgresql_where=(Customer.is_deleted == False)
)