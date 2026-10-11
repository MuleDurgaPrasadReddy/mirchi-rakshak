from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FarmBase(BaseModel):
    name: str
    variety: Optional[str] = None
    size_acres: Optional[float] = None
    village: Optional[str] = None
    planting_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    variety: Optional[str] = None
    size_acres: Optional[float] = None
    village: Optional[str] = None
    planting_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FarmResponse(FarmBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
