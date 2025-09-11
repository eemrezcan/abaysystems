# app/models/system_profile_template.py

import uuid
from sqlalchemy import Column, String, ForeignKey, Integer,Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class SystemProfileTemplate(Base):
    __tablename__ = "system_profile_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_variant_id = Column(UUID(as_uuid=True), ForeignKey("system_variant.id", ondelete="CASCADE"), nullable=False)
    profile_id        = Column(UUID(as_uuid=True), ForeignKey("profile.id"), nullable=False)
    formula_cut_length = Column(String, nullable=False)
    formula_cut_count  = Column(String, nullable=False)
    order_index        = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    # --- Yeni alan ---
    is_painted = Column(Boolean, nullable=False, default=False)  # NEW

    # ilişki (opsiyonel, kullanmak isterseniz)
    variant = relationship("SystemVariant", back_populates="profile_templates")
    profile = relationship("Profile")
