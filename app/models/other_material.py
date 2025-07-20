# app/models/other_material.py
import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class OtherMaterial(Base):
    __tablename__ = "other_material"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diger_malzeme_isim = Column(String(100), nullable=False)
    birim = Column(String(20), nullable=False)
    birim_agirlik = Column(Numeric, nullable=False)
    hesaplama_turu = Column(String(20), nullable=True)
