# app/models/remote.py

import uuid
from sqlalchemy import Column, String, Numeric, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func, expression

from app.db.base import Base

class Remote(Base):
    __tablename__ = "remote"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kumanda_isim  = Column(String(100), nullable=False)
    price         = Column(Numeric, nullable=False)      # TL (istersen Numeric(12,2) yapabiliriz)
    kapasite      = Column(Integer, nullable=False)      # ör: kanal/sürgü sayısı vb.
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # soft state alanları (glass_type ile aynı mantık)
    is_active     = Column(Boolean, nullable=False, server_default=expression.true())
    is_deleted    = Column(Boolean, nullable=False, server_default=expression.false())
