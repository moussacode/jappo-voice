from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transcription import router as transcription_router
from app.routes.synthesis import router as synthesis_router
from app.routes.health import router as health_router
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JAPPO Voice Service",
    description="Service de transcription Whisper et de synthèse vocale TTS pour JAPPO",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(transcription_router, prefix="/api/voice", tags=["transcription"])
app.include_router(synthesis_router, prefix="/api/voice", tags=["synthesis"])


@app.on_event("startup")
async def startup_event():
    logger.info("JAPPO Voice Service démarrage...")
    logger.info(f"Port       : {settings.voice_port}")
    logger.info(f"Modèle STT : {settings.whisper_model}")
    logger.info(f"Modèle TTS : {settings.tts_model}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("JAPPO Voice Service arrêt.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.voice_host,
        port=settings.voice_port,
        reload=True,
    )
