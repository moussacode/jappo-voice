from pydantic import BaseModel, Field
from typing import Optional


class TranscriptionResponse(BaseModel):
    success: bool
    text: str = ""
    language: str = "fr"
    duration: float = 0.0
    error: Optional[str] = None


class TranscriptionError(BaseModel):
    success: bool = False
    error: dict
