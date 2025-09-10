# app/models/system_material_template.py

import uuid
from sqlalchemy import Column, String, ForeignKey, Integer,Boolean, Numeric
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
    formula_cut_length = Column(String, nullable=True)
    # 💲 Opsiyonel birim fiyat (material.unit_price üzerine şablon bazında override edilebilir)
    unit_price        = Column(Numeric, nullable=True)
    
    # ✅ İSTENEN GÜNCEL: Serbest metin, 50 karakter, nullable
    type = Column(String(50), nullable=True)

    # Zaten nullable; adetli hesaplar vb. için parça boyu (mm)
    piece_length_mm = Column(Integer, nullable=True)
    
    order_index = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

        # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    variant  = relationship("SystemVariant", back_populates="material_templates")
    material = relationship("OtherMaterial")
