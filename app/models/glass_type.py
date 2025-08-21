# app/models/glass_type.py

import uuid
from sqlalchemy import Column, String, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func, expression

from app.db.base import Base

class GlassType(Base):
    __tablename__ = "glass_type"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cam_isim     = Column(String(100), nullable=False)
    thickness_mm = Column(Numeric, nullable=False)
    # birim_agirlik sütunu kaldırıldı
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at   = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # ✅ soft delete / aktiflik
    is_active  = Column(Boolean, nullable=False, server_default=expression.true())
    is_deleted = Column(Boolean, nullable=False, server_default=expression.false())