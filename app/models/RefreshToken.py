# app/models/refresh_token.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True, nullable=False)

    # Opaque token’ın sunucuda saklanan SHA-256 hash’i
    token_hash = Column(String(64), unique=True, nullable=False)

    user_agent = Column(String(256), nullable=True)
    ip_address = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    revoked_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by = Column(UUID(as_uuid=True), nullable=True)  # rotasyon takibi (opsiyonel)

    user = relationship("AppUser", backref="refresh_tokens")

Index("ix_refresh_token_valid", RefreshToken.user_id, RefreshToken.expires_at)
