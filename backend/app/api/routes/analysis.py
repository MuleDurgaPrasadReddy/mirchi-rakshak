from fastapi import APIRouter, Depends
from app.schemas.analysis import AnalysisRequest, AnalysisResult
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/scan", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_crop_image(request: AnalysisRequest, user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint for AI image diagnosis & subject verification.
    """
    return AnalysisResult(
        is_chili_leaf=True,
        disease="Healthy Chili Crop",
        is_healthy=True,
        confidence=92,
        severity="None",
        affected_area="Intact vibrant green leaves with robust canopy",
        risk_level="Low",
        recommendation="Favourable crop growth. Continue regular monitoring.",
        treatment=[],
        recovery_days=0,
    )
