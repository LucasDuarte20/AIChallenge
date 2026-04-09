from typing import Optional, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    material_code: Optional[str] = None
    material_mlfb: Optional[str] = None
    data: Optional[Any] = None
    confidence: float = 1.0
