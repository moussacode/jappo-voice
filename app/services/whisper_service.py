"""
Service de transcription audio → texte via OpenAI Whisper.

Utilise le package `openai-whisper` (modèle local) par défaut.
La stratégie de chargement est lazy : le modèle n'est chargé qu'au premier appel
afin de ne pas bloquer le démarrage de l'application.

Pour utiliser l'API Whisper d'OpenAI à la place (cloud, sans GPU local),
passez tts_model="openai" dans .env et ajoutez OPENAI_API_KEY.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Le modèle Whisper est chargé en lazy (None = non encore chargé)
_whisper_model = None


def _get_model(model_name: str):
    """Charge et met en cache le modèle Whisper (singleton)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper  # openai-whisper
            logger.info(f"[Whisper] Chargement du modèle '{model_name}'...")
            _whisper_model = whisper.load_model(model_name)
            logger.info("[Whisper] Modèle chargé.")
        except ImportError:
            raise RuntimeError(
                "Le package 'openai-whisper' n'est pas installé. "
                "Exécutez : pip install openai-whisper"
            )
    return _whisper_model


class WhisperService:
    """Transcrit un fichier audio en texte via Whisper local."""

    def __init__(self, model_name: str = "base", device: str = "cpu", language: str = "fr"):
        self.model_name = model_name
        self.device = device
        self.default_language = language

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None,
    ) -> dict:
        """
        Transcrit les bytes audio.

        Retourne un dict :
        {
            "success": bool,
            "text": str,
            "language": str,
            "duration": float,
        }
        """
        lang = language or self.default_language
        tmp_path: Optional[str] = None

        try:
            # Écrire les bytes dans un fichier temporaire
            suffix = Path(filename).suffix or ".webm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            logger.info(
                f"[Whisper] Transcription de {filename} "
                f"({len(audio_bytes) / 1024:.1f} Ko, langue='{lang}')..."
            )

            start = time.monotonic()

            # Exécution dans un thread dédié pour ne pas bloquer la boucle asyncio
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_transcription,
                tmp_path,
                lang,
            )

            duration = time.monotonic() - start
            logger.info(f"[Whisper] Terminé en {duration:.2f}s — texte : '{result['text'][:80]}...'")

            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result.get("language", lang),
                "duration": round(duration, 2),
            }

        except Exception as e:
            logger.error(f"[Whisper] Erreur lors de la transcription : {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "language": lang,
                "duration": 0.0,
                "error": str(e),
            }
        finally:
            # Nettoyage du fichier temporaire
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _run_transcription(self, file_path: str, language: str) -> dict:
        """Tâche synchrone exécutée dans un thread séparé."""
        model = _get_model(self.model_name)
        # language=None → Whisper auto-détecte
        return model.transcribe(
            file_path,
            language=language if language and language.lower() != "auto" else None,
            fp16=False,  # fp16=False pour CPU
        )
