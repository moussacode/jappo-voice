from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration du service vocal JAPPO."""

    # Serveur
    voice_host: str = "0.0.0.0"
    voice_port: int = 8001

    # Sécurité
    ai_orchestrator_api_key: str = ""

    # Whisper (Speech-to-Text)
    # Modèles disponibles : tiny, base, small, medium, large
    # tiny/base -> rapide, petite mémoire ; large -> meilleure précision
    whisper_model: str = "base"
    whisper_language: str = "fr"       # Langue par défaut ; None = auto-detect
    whisper_device: str = "cpu"        # "cpu" ou "cuda"

    # TTS (Text-to-Speech)
    # Fournisseur : "gtts" (gTTS, gratuit) | "openai" | "coqui"
    tts_model: str = "gtts"
    tts_language: str = "fr"

    # Limites audio
    max_audio_size_mb: int = 25        # Taille maximale du fichier audio (Mo)
    max_audio_duration_sec: int = 120  # Durée maximale (secondes)
    transcription_timeout_sec: int = 60

    # Formats acceptés
    allowed_audio_formats: list[str] = ["audio/mpeg", "audio/wav", "audio/ogg",
                                         "audio/webm", "audio/mp4", "audio/x-m4a"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
