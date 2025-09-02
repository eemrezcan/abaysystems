# app/models/system_remote_template.py

import uuid
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class SystemRemoteTemplate(Base):
    __tablename__ = "system_remote_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # İlişkiler
    system_variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("system_variant.id", ondelete="CASCADE"),
        nullable=False
    )
    remote_id = Column(
        UUID(as_uuid=True),
        ForeignKey("remote.id"),
        nullable=False
    )

    # Sıralama
    order_index = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # ORM ilişkileri
    variant = relationship("SystemVariant", back_populates="remote_templates")
    remote  = relationship("Remote")
