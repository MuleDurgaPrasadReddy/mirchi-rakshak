from typing import Optional, List
from pydantic import BaseModel
from app.schemas.scan import TreatmentStep


class LeafImageStats(BaseModel):
    greenRatio: Optional[float] = 0.0
    foliageRatio: Optional[float] = 0.0
    skinRatio: Optional[float] = 0.0
    brownSpotRatio: Optional[float] = 0.0
    yellowRatio: Optional[float] = 0.0
    darkGreenRatio: Optional[float] = 0.0
    glossyRatio: Optional[float] = 0.0


class AnalysisRequest(BaseModel):
    imageBase64: Optional[str] = None
    imageUrl: Optional[str] = None
    language: Optional[str] = "en"
    imageStats: Optional[LeafImageStats] = None
    predictedClass: Optional[str] = None


class AnalysisResult(BaseModel):
    is_chili_leaf: bool = True
    invalid_reason: Optional[str] = None
    disease: str
    is_healthy: bool = False
    confidence: int = 0
    severity: str = "None"
    affected_area: str = "N/A"
    risk_level: str = "Low"
    recommendation: str = ""
    treatment: List[TreatmentStep] = []
    recovery_days: int = 0
