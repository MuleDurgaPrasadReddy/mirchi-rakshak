from typing import List, Dict
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_id
from app.schemas.scan import ScanCreate, ScanResponse

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=List[Dict[str, str]])
async def get_scan_history(user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to retrieve user scan history.
    """
    return [
        {"id": "scan-1", "user_id": user_id, "disease": "Healthy Chili Crop", "confidence": "92"}
    ]


@router.post("", response_model=Dict[str, str])
async def save_scan_record(scan: ScanCreate, user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to save scan result record.
    """
    return {
        "id": "scan-new",
        "user_id": user_id,
        "message": "Scan record saved placeholder",
    }
