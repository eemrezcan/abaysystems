# app/models/other_material.py

import uuid
from sqlalchemy import Column, String, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func, expression  # ✅ eklendi

from app.db.base import Base

class OtherMaterial(Base):
    __tablename__ = "other_material"

    id                  = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diger_malzeme_isim  = Column(String(100), nullable=False)
    birim               = Column(String(20), nullable=False)
    birim_agirlik       = Column(Numeric, nullable=False)
    hesaplama_turu      = Column(String(20), nullable=True)
    created_at          = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at          = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # ✅ soft delete / aktiflik
    is_active  = Column(Boolean, nullable=False, server_default=expression.true())
    is_deleted = Column(Boolean, nullable=False, server_default=expression.false())
