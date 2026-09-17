"""
Route de synthèse vocale texte → audio.

POST /api/voice/synthesize
  - Body JSON : { "text": "...", "language": "fr" }
  - Retourne les bytes audio (MP3 ou WAV selon le fournisseur TTS)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.config import settings
from app.schemas.synthesis import SynthesisRequest
from app.services.tts_service import TTSService, create_tts_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton du service TTS
_tts: Optional[TTSService] = None


def _get_tts() -> TTSService:
    global _tts
    if _tts is None:
        _tts = create_tts_service(provider=settings.tts_model)
    return _tts


@router.post(
    "/synthesize",
    summary="Synthétiser un texte en audio",
    response_description="Fichier audio (MP3 ou WAV)",
    responses={
        200: {"content": {"audio/mpeg": {}, "audio/wav": {}}},
        400: {"description": "Texte vide ou trop long"},
        500: {"description": "Erreur de synthèse"},
    },
)
async def synthesize(request: SynthesisRequest) -> Response:
    """
    Convertit un texte en audio via le service TTS configuré.

    Le fichier audio retourné est directement exploitable par Angular
    via `new Audio(URL.createObjectURL(blob))`.

    Exemple :
    ```json
    POST /api/voice/synthesize
    {
        "text": "Votre projet Pamoja a été modifié.",
        "language": "fr"
    }
    ```
    → Retourne les bytes audio MP3/WAV.
    """
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_TEXT", "message": "Le texte à synthétiser est vide."},
        )

    tts_svc = _get_tts()

    try:
        audio_bytes = await tts_svc.synthesize(text=text, language=request.language)
    except Exception as e:
        logger.error(f"[Synthesis] Erreur : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SYNTHESIS_FAILED",
                "message": "La synthèse vocale a échoué.",
            },
        )

    return Response(
        content=audio_bytes,
        media_type=tts_svc.audio_format(),
        headers={
            "Content-Disposition": 'inline; filename="response.mp3"',
            "Cache-Control": "no-store",
        },
    )
