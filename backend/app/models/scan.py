import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Column, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id = Column(String, ForeignKey("farms.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(String, nullable=True)
    is_chili_leaf = Column(Boolean, default=True, nullable=True)
    invalid_reason = Column(String, nullable=True)
    disease = Column(String, nullable=True)
    is_healthy = Column(Boolean, nullable=True)
    confidence = Column(Integer, nullable=True)
    severity = Column(String, nullable=True)
    affected_area = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)
    treatment = Column(JSON, nullable=True)
    recovery_days = Column(Integer, nullable=True)
    language = Column(String, default="en", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("Profile", back_populates="scans")
    farm = relationship("Farm", back_populates="scans")
