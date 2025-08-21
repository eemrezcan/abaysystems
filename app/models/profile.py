# app/models/profile.py
import uuid
from sqlalchemy import Column, String, Numeric, TEXT, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func, expression

from app.db.base import Base

class Profile(Base):
    __tablename__ = "profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profil_kodu = Column(String(50), unique=True, nullable=False)
    profil_isim = Column(String(100), nullable=False)
    profil_kesit_fotograf = Column(TEXT, nullable=True)
    birim_agirlik = Column(Numeric, nullable=False)
    boy_uzunluk = Column(Numeric, nullable=False)
    unit_price = Column(Numeric, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # ✅ soft delete / aktiflik
    is_active  = Column(Boolean, nullable=False, server_default=expression.true())
    is_deleted = Column(Boolean, nullable=False, server_default=expression.false())

