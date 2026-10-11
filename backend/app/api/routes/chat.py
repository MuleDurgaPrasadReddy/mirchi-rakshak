from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest, user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint for AI farmer chat assistant.
    """
    return ChatResponse(
        reply="MirchiRakshak AI Chat Assistant foundation ready."
    )
