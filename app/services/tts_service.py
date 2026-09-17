"""
Service de synthèse vocale (Text-to-Speech).

Architecture : classe abstraite TTSService + implémentations concrètes.
Permet de changer de fournisseur TTS sans modifier le reste de l'application.

Fournisseurs disponibles :
- GTTSProvider  : Google Text-to-Speech (gratuit, requiert connexion internet)
- CoquiProvider : Coqui TTS (local, open-source, meilleure qualité)

Le fournisseur actif est sélectionné via la variable d'env TTS_MODEL.
"""

import io
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# ── Interface abstraite ───────────────────────────────────────────────────────

class TTSService(ABC):
    """Interface commune pour tous les fournisseurs TTS."""

    @abstractmethod
    async def synthesize(self, text: str, language: str = "fr") -> bytes:
        """
        Convertit le texte en audio.

        Retourne les bytes MP3/WAV exploitables directement par Angular.
        Lève une exception en cas d'erreur.
        """
        ...

    @abstractmethod
    def audio_format(self) -> str:
        """Retourne le Content-Type MIME (ex: 'audio/mpeg')."""
        ...


# ── Implémentation gTTS ───────────────────────────────────────────────────────

class GTTSProvider(TTSService):
    """
    Google Text-to-Speech via le package gTTS.

    Avantages : gratuit, pas de clé API, bonne qualité en français.
    Inconvénient : requiert une connexion internet ; latence réseau.
    """

    async def synthesize(self, text: str, language: str = "fr") -> bytes:
        try:
            from gtts import gTTS
        except ImportError:
            raise RuntimeError(
                "Le package 'gtts' n'est pas installé. "
                "Exécutez : pip install gtts"
            )

        import asyncio

        def _run() -> bytes:
            tts = gTTS(text=text, lang=language, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            return buf.getvalue()

        logger.info(f"[gTTS] Synthèse : '{text[:60]}...' (lang={language})")
        audio_bytes = await asyncio.get_event_loop().run_in_executor(None, _run)
        logger.info(f"[gTTS] Synthèse terminée — {len(audio_bytes)} octets")
        return audio_bytes

    def audio_format(self) -> str:
        return "audio/mpeg"


# ── Implémentation Coqui TTS (local) ─────────────────────────────────────────

class CoquiProvider(TTSService):
    """
    Coqui TTS — modèle local open-source haute qualité.

    Avantages : aucune connexion requise, qualité élevée, supporte le français.
    Inconvénient : temps de chargement du modèle, RAM/GPU nécessaire.

    Installation : pip install TTS
    """

    def __init__(self, model_name: Optional[str] = None):
        # Modèle VITS francophone recommandé
        self.model_name = model_name or "tts_models/fr/mai/tacotron2-DDC"
        self._tts = None  # Lazy load

    def _get_tts(self):
        if self._tts is None:
            try:
                from TTS.api import TTS
                logger.info(f"[Coqui] Chargement du modèle TTS '{self.model_name}'...")
                self._tts = TTS(model_name=self.model_name)
                logger.info("[Coqui] Modèle chargé.")
            except ImportError:
                raise RuntimeError(
                    "Le package 'TTS' n'est pas installé. "
                    "Exécutez : pip install TTS"
                )
        return self._tts

    async def synthesize(self, text: str, language: str = "fr") -> bytes:
        import asyncio
        import tempfile
        import os

        def _run() -> bytes:
            tts = self._get_tts()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                tts.tts_to_file(text=text, file_path=tmp_path)
                with open(tmp_path, "rb") as f:
                    return f.read()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        logger.info(f"[Coqui] Synthèse : '{text[:60]}...'")
        audio_bytes = await asyncio.get_event_loop().run_in_executor(None, _run)
        logger.info(f"[Coqui] Synthèse terminée — {len(audio_bytes)} octets")
        return audio_bytes

    def audio_format(self) -> str:
        return "audio/wav"


# ── Factory ───────────────────────────────────────────────────────────────────

def create_tts_service(provider: str = "gtts", **kwargs) -> TTSService:
    """
    Instancie le bon fournisseur TTS selon la configuration.

    Valeurs acceptées pour `provider` :
    - "gtts"  → GTTSProvider (défaut, gratuit)
    - "coqui" → CoquiProvider (local, haute qualité)
    """
    provider = provider.lower()
    if provider == "gtts":
        return GTTSProvider()
    elif provider == "coqui":
        return CoquiProvider(model_name=kwargs.get("model_name"))
    else:
        logger.warning(f"[TTS] Fournisseur inconnu '{provider}', fallback sur gTTS.")
        return GTTSProvider()
