# app/models/project_code_ledger.py
from sqlalchemy import Column, BigInteger, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, Index
from app.db.base import Base

class ProjectCodeLedger(Base):
    """
    Her owner için kullanılan numaraların defteri.
    (owner_id, number) -> PRIMARY KEY: aynı number aynı owner için asla tekrar kullanılmaz.
    """
    __tablename__ = "project_code_ledger"

    owner_id     = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    number       = Column(BigInteger, nullable=False)  # kullanılmış sayı
    project_id   = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="SET NULL"), nullable=True)
    project_kodu = Column(String(50), nullable=True)   # bilgilendirme/iz sürme amaçlı
    used_at      = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("owner_id", "number", name="pk_project_code_ledger"),
        Index("ix_pcl_owner", "owner_id"),
        Index("ix_pcl_owner_number", "owner_id", "number"),
    )
