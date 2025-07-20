# app/models/glass_type.py
import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.base import Base

class GlassType(Base):
    __tablename__ = "glass_type"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cam_isim = Column(String(100), nullable=False)
    thickness_mm = Column(Numeric, nullable=False)
    birim_agirlik = Column(Numeric, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
