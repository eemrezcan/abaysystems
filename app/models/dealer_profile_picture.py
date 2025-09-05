# app/models/dealer_profile_picture.py
from uuid import uuid4
from sqlalchemy import Column, Text, TIMESTAMP, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base  # Projene göre import yolunu koru/düzelt

class DealerProfilePicture(Base):
    __tablename__ = "dealer_profile_picture"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    image_url  = Column(Text, nullable=False)   # Örn: /static/dealers/<user_id>/profile.<ext>
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_dealer_profile_picture_user"),
    )
