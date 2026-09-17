"""
Route de transcription audio → texte.

POST /api/voice/transcribe
  - Accepte un fichier audio multipart (champ `file`)
  - Optionnel : champ `language` (ex: "fr", "en", "auto")
  - Retourne la transcription JSON
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.schemas.transcription import TranscriptionResponse
from app.services.whisper_service import WhisperService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton du service Whisper — partagé entre les requêtes
_whisper: Optional[WhisperService] = None


def _get_whisper() -> WhisperService:
    global _whisper
    if _whisper is None:
        _whisper = WhisperService(
            model_name=settings.whisper_model,
            device=settings.whisper_device,
            language=settings.whisper_language,
        )
    return _whisper


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcrire un fichier audio en texte",
)
async def transcribe(
    file: UploadFile = File(..., description="Fichier audio (WAV, MP3, OGG, WebM, MP4)"),
    language: Optional[str] = Form(default=None, description="Langue (fr, en, auto…)"),
) -> TranscriptionResponse:
    """
    Transcrit un fichier audio en texte via Whisper.

    Limites :
    - Taille maximale : MAX_AUDIO_SIZE_MB Mo (défaut 25 Mo)
    - Formats acceptés : WAV, MP3, OGG, WebM, MP4

    Exemple de réponse :
    ```json
    {
        "success": true,
        "text": "Archive mon projet Pamoja",
        "language": "fr",
        "duration": 4.8
    }
    ```
    """
    # ── Validation du format ────────────────────────────────────────────────
    content_type = (file.content_type or "").lower().split(";")[0].strip()

    if content_type not in settings.allowed_audio_formats:
        logger.warning(f"[Transcription] Format refusé : {content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "UNSUPPORTED_AUDIO_FORMAT",
                "message": f"Format audio non supporté : {content_type}. "
                           f"Formats acceptés : {', '.join(settings.allowed_audio_formats)}",
            },
        )

    # ── Lecture des bytes ───────────────────────────────────────────────────
    audio_bytes = await file.read()

    # ── Validation de la taille ─────────────────────────────────────────────
    max_bytes = settings.max_audio_size_mb * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        logger.warning(
            f"[Transcription] Fichier trop grand : {len(audio_bytes) / 1024 / 1024:.1f} Mo "
            f"(max {settings.max_audio_size_mb} Mo)"
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "AUDIO_TOO_LARGE",
                "message": f"Le fichier audio dépasse {settings.max_audio_size_mb} Mo.",
            },
        )

    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_AUDIO", "message": "Le fichier audio est vide."},
        )

    # ── Transcription ───────────────────────────────────────────────────────
    whisper_svc = _get_whisper()
    result = await whisper_svc.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "audio",
        language=language,
    )

    if not result["success"]:
        logger.error(f"[Transcription] Échec : {result.get('error', 'unknown')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TRANSCRIPTION_FAILED",
                "message": "La transcription audio a échoué.",
            },
        )

    return TranscriptionResponse(
        success=True,
        text=result["text"],
        language=result["language"],
        duration=result["duration"],
    )
