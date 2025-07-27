import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.base import Base

class Color(Base):
    __tablename__ = "color"

    id         = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(50), nullable=False)                      # Örn: "RAL 7039"
    type       = Column(String(20), nullable=False)                      # "profile" veya "glass"
    unit_cost  = Column(Numeric, nullable=False)                         # TL/kg (profil) veya TL/m² (cam)

    def __repr__(self):
        return f"<Color name={self.name} type={self.type} cost={self.unit_cost}>"
