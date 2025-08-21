# app/models/system.py

import uuid
from sqlalchemy import Column, String, TEXT, Numeric, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func, expression 
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
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

    # Bir system birden fazla varyanta sahiptir
    variants = relationship(
        "SystemVariant",
        back_populates="system",
        cascade="all, delete-orphan"
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
    photo_url = Column(String(300), nullable=True) 
    # max_width_m ve max_height_m sütunları kaldırıldı
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ publish + soft delete
    is_published = Column(Boolean, nullable=False, server_default=expression.false())
    is_deleted   = Column(Boolean, nullable=False, server_default=expression.false())

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
