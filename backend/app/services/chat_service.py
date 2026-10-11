from typing import List, Dict
from app.schemas.chat import ChatMessage


class ChatService:
    async def process_chat_message(self, messages: List[ChatMessage], language: str = "en") -> str:
        """
        Placeholder method for Processing farmer AI chat queries.
        """
        return "MirchiRakshak AI Chat Assistant scaffolded successfully."


chat_service = ChatService()
