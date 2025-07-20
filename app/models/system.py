# app/models/system.py

import uuid
from sqlalchemy import Column, String, TEXT, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.base import Base

class System(Base):
    __tablename__ = "system"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(TEXT, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Bir system birden fazla varyanta sahiptir
    variants = relationship(
        "SystemVariant",
        back_populates="system",
        cascade="all, delete-orphan"
    )


class SystemVariant(Base):
    __tablename__ = "system_variant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id   = Column(
        UUID(as_uuid=True),
        ForeignKey("system.id", ondelete="CASCADE"),
        nullable=False
    )
    name        = Column(String(100), nullable=False)
    max_width_m = Column(Numeric, nullable=True)
    max_height_m   = Column(Numeric, nullable=True)
    color_options  = Column(ARRAY(String), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # System ile iki yönlü ilişki
    system = relationship("System", back_populates="variants")

    # Template tablolarıyla ilişkiler
    profile_templates = relationship(
        "SystemProfileTemplate",
        back_populates="variant",
        cascade="all, delete-orphan"
    )
    glass_templates = relationship(
        "SystemGlassTemplate",
        back_populates="variant",
        cascade="all, delete-orphan"
    )
    material_templates = relationship(
        "SystemMaterialTemplate",
        back_populates="variant",
        cascade="all, delete-orphan"
    )
