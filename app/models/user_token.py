# app/models/user_token.py
import uuid
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class UserToken(Base):
    __tablename__ = "user_token"

    id          = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    type        = Column(String(20), nullable=False)   # "invite" | "reset"
    token_hash  = Column(String(64), unique=True, nullable=False)  # sha256 hex
    expires_at  = Column(TIMESTAMP(timezone=True), nullable=False)
    used_at     = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("AppUser", backref="tokens")

# Sık sorgular için indeksler
Index("ix_user_token_user_type", UserToken.user_id, UserToken.type)
Index("ix_user_token_expires", UserToken.expires_at)
