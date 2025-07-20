# app/models/system_material_template.py

import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class SystemMaterialTemplate(Base):
    __tablename__ = "system_material_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_variant_id = Column(UUID(as_uuid=True), ForeignKey("system_variant.id", ondelete="CASCADE"), nullable=False)
    material_id       = Column(UUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    formula_quantity  = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    variant  = relationship("SystemVariant", back_populates="material_templates")
    material = relationship("OtherMaterial")
