from typing import List, Literal
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: str = "en"


class ChatResponse(BaseModel):
    reply: str
