# app/models/calculation_helper.py

import uuid
from sqlalchemy import Column, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.base import Base


class CalculationHelper(Base):
    __tablename__ = "calculation_helper"

    id         = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id   = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=True)
    bicak_payi = Column(Numeric, nullable=False, server_default="0")
    boya_payi  = Column(Numeric, nullable=False, server_default="0")

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
