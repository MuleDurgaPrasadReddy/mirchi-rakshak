from typing import List, Dict
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_id
from app.schemas.farm import FarmCreate, FarmResponse

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("", response_model=List[Dict[str, str]])
async def list_farms(user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to list user farms.
    """
    return [
        {"id": "farm-1", "name": "Guntur Sannam Field", "user_id": user_id}
    ]


@router.post("", response_model=Dict[str, str])
async def create_farm(farm: FarmCreate, user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to create a new farm field.
    """
    return {
        "id": "farm-new",
        "name": farm.name,
        "user_id": user_id,
        "message": "Farm created placeholder",
    }
