from pydantic import BaseModel, Field
from typing import Optional


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000,
                      description="Texte à convertir en audio")
    language: str = Field(default="fr", description="Code langue ISO 639-1 (ex: fr, en)")


class SynthesisError(BaseModel):
    success: bool = False
    error: dict
