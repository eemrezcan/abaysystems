# app/models/pdf.py
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, TIMESTAMP, func, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

class PdfTitleTemplate(Base):
    __tablename__ = "pdf_title_template"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id    = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)  # NEW
    key         = Column(String(100), nullable=False, index=True)
    config_json = Column(JSONB, nullable=False)
    is_deleted  = Column(Boolean, nullable=False, default=False)

    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_id", "key", name="uq_pdf_title_template_owner_key"),  # NEW
    )

class PdfBrand(Base):
    __tablename__ = "pdf_brand"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id    = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)  # NEW
    key         = Column(String(100), nullable=False, index=True)
    config_json = Column(JSONB, nullable=False)
    logo_url    = Column(Text, nullable=True)
    is_deleted  = Column(Boolean, nullable=False, default=False)

    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_id", "key", name="uq_pdf_brand_owner_key"),  # NEW
    )
