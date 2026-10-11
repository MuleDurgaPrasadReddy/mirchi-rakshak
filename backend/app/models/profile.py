from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Column
from sqlalchemy.orm import relationship
from app.db.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)  # UUID string matching auth.users(id)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    language = Column(String, default="en", nullable=False)
    district = Column(String, nullable=True)
    village = Column(String, nullable=True)
    onboarded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
