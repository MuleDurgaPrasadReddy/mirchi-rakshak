import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Column, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    variety = Column(String, nullable=True)
    size_acres = Column(Float, nullable=True)
    village = Column(String, nullable=True)
    planting_date = Column(Date, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("Profile", back_populates="farms")
    scans = relationship("Scan", back_populates="farm")
