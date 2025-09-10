
# app/models/project_code_rule.py
import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, Index
from app.db.base import Base

class ProjectCodeRule(Base):
    """
    Her bayi (owner) için tam 1 kayıt:
    - owner_id UNIQUE
    - prefix artık GLOBAL UNIQUE DEĞİL (birden fazla kullanıcı aynı prefix'i seçebilir)
    - start_number: ilk verilecek sayı (örn. 10)
    - current_number: son verilen sayı (ilk kurulumda start_number-1 set edilir)
    - separator/padding: format ayarları (örn. '-', 5 => BALU-00010)
    """
    __tablename__ = "project_code_rule"

    id             = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id       = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"),
                             nullable=False, unique=True, index=True)
    # ⬇️ prefix artık unique=False
    prefix         = Column(String(32), nullable=False, index=True)
    separator      = Column(String(5), nullable=False, default="-")
    padding        = Column(BigInteger, nullable=False, default=0)   # 0 => pad yok; 5 => 00010
    start_number   = Column(BigInteger, nullable=False, default=1)
    current_number = Column(BigInteger, nullable=False, default=0)   # start_number - 1 ile başlat
    is_active      = Column(Boolean, nullable=False, default=True)

    created_at     = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("padding >= 0", name="ck_pcr_padding_nonneg"),
        CheckConstraint("start_number >= 0", name="ck_pcr_start_nonneg"),
        CheckConstraint("current_number >= 0", name="ck_pcr_current_nonneg"),
        Index("ix_pcr_owner", "owner_id"),
        Index("ix_pcr_prefix", "prefix"),  # normal (non-unique) index
    )

    created_at     = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("padding >= 0", name="ck_pcr_padding_nonneg"),
        CheckConstraint("start_number >= 0", name="ck_pcr_start_nonneg"),
        CheckConstraint("current_number >= 0", name="ck_pcr_current_nonneg"),
        Index("ix_pcr_owner", "owner_id"),
        Index("ix_pcr_prefix", "prefix"),
    )
