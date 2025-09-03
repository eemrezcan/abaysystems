# app/models/system_glass_template.py

import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class SystemGlassTemplate(Base):
    __tablename__ = "system_glass_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_variant_id = Column(UUID(as_uuid=True), ForeignKey("system_variant.id", ondelete="CASCADE"), nullable=False)
    glass_type_id     = Column(UUID(as_uuid=True), ForeignKey("glass_type.id"), nullable=False)
    formula_width    = Column(String, nullable=False)
    formula_height   = Column(String, nullable=False)
    formula_count    = Column(String, nullable=False)
    order_index = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    variant    = relationship("SystemVariant", back_populates="glass_templates")
    glass_type = relationship("GlassType")
