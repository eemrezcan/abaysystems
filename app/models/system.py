# app/models/system.py

import uuid
from sqlalchemy import Column, String, TEXT, Numeric, ForeignKey, Boolean, event, update, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func, expression
from sqlalchemy.orm import relationship

from app.db.base import Base


class System(Base):
    __tablename__ = "system"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(TEXT, nullable=True)
    photo_url = Column(String(300), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ publish + soft delete
    is_published = Column(Boolean, nullable=False, server_default=expression.false())
    is_deleted   = Column(Boolean, nullable=False, server_default=expression.false())

    # ✅ aktif/pasif etiketi
    is_active = Column(Boolean, nullable=False, server_default=expression.true())

    # ✅ Liste sırası (küçük -> önce). Varsayılan 0
    sort_index = Column(Integer, nullable=False, server_default="0")

    # Bir system birden fazla varyanta sahiptir
    variants = relationship(
        "SystemVariant",
        back_populates="system",
        cascade="all, delete-orphan",
        order_by=lambda: SystemVariant.sort_index.asc()  # ✅ güvenli
    )


    # DB indeksleri
    __table_args__ = (
        Index("ix_system_sort_index", "sort_index"),
    )


class SystemVariant(Base):
    __tablename__ = "system_variant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("system.id", ondelete="CASCADE"),
        nullable=False
    )
    name          = Column(String(100), nullable=False)
    photo_url     = Column(String(300), nullable=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ publish + soft delete
    is_published = Column(Boolean, nullable=False, server_default=expression.false())
    is_deleted   = Column(Boolean, nullable=False, server_default=expression.false())

    # ✅ aktif/pasif etiketi
    is_active = Column(Boolean, nullable=False, server_default=expression.true())

    # ✅ Aynı system içindeki liste sırası (küçük -> önce). Varsayılan 0
    sort_index = Column(Integer, nullable=False, server_default="0")

    # System ile iki yönlü ilişki
    system = relationship("System", back_populates="variants")

    # Template tablolarıyla ilişkiler
    profile_templates  = relationship(
        "SystemProfileTemplate",
        back_populates="variant",
        cascade="all, delete-orphan",
    )
    glass_templates    = relationship(
        "SystemGlassTemplate",
        back_populates="variant",
        cascade="all, delete-orphan",
    )
    material_templates = relationship(
        "SystemMaterialTemplate",
        back_populates="variant",
        cascade="all, delete-orphan",
    )
    remote_templates = relationship(
        "SystemRemoteTemplate",
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # DB indeksleri
    __table_args__ = (
        Index("ix_system_variant_system_sort_index", "system_id", "sort_index"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Otomatik senkron: Bir System is_active = false yapılırsa, tüm varyantlarını da
# false'a çevir. true yapılırsa varyantları zorla true yapmıyoruz (manuel kalabilir).
# Bu mantık "model seviyesi"nde garanti edilir.
# ─────────────────────────────────────────────────────────────────────────────
@event.listens_for(System, "after_update")
def system_after_update(mapper, connection, target: System):
    # Sadece false'a geçişi zorunlu kapatma sayıyoruz
    if target.is_active is False:
        connection.execute(
            update(SystemVariant)
            .where(SystemVariant.system_id == target.id)
            .values(is_active=False)
        )
