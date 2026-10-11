from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class TreatmentStep(BaseModel):
    step: str
    detail: str


class ScanBase(BaseModel):
    image_url: Optional[str] = None
    is_chili_leaf: Optional[bool] = True
    invalid_reason: Optional[str] = None
    disease: Optional[str] = None
    is_healthy: Optional[bool] = None
    confidence: Optional[int] = None
    severity: Optional[str] = None
    affected_area: Optional[str] = None
    risk_level: Optional[str] = None
    recommendation: Optional[str] = None
    treatment: Optional[List[TreatmentStep]] = None
    recovery_days: Optional[int] = None
    language: Optional[str] = "en"
    farm_id: Optional[str] = None


class ScanCreate(ScanBase):
    pass


class ScanResponse(ScanBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
