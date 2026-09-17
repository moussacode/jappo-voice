# jappo-voice

Service vocal JAPPO — Whisper (STT) + TTS.

Port : **8001**

## Démarrage rapide

```bash
cd jappo-voice

# Créer le venv
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt

# Installer Whisper (STT)
pip install openai-whisper

# Démarrer
uvicorn app.main:app --reload --port 8001
```

## Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/health` | Santé du service |
| POST | `/api/voice/transcribe` | Audio → Texte (Whisper) |
| POST | `/api/voice/synthesize` | Texte → Audio (TTS) |

## Exemple transcription

```bash
curl -X POST http://localhost:8001/api/voice/transcribe \
  -F "file=@mon_audio.webm" \
  -F "language=fr"
```

Réponse :
```json
{
  "success": true,
  "text": "Archive mon projet Pamoja",
  "language": "fr",
  "duration": 4.8
}
```

## Exemple synthèse vocale

```bash
curl -X POST http://localhost:8001/api/voice/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Votre projet Pamoja a été modifié.", "language": "fr"}' \
  --output response.mp3
```

## Architecture

```
jappo-voice/
├── app/
│   ├── main.py            # FastAPI app + CORS
│   ├── config.py          # Settings (.env)
│   ├── routes/
│   │   ├── health.py      # GET /health
│   │   ├── transcription.py # POST /api/voice/transcribe
│   │   └── synthesis.py   # POST /api/voice/synthesize
│   ├── services/
│   │   ├── whisper_service.py  # Whisper (lazy load, thread pool)
│   │   └── tts_service.py      # TTSService abstrait + GTTSProvider + CoquiProvider
│   └── schemas/
│       ├── transcription.py
│       └── synthesis.py
├── requirements.txt
└── .env
```

## Fournisseurs TTS

| Fournisseur | Config (`TTS_MODEL`) | Qualité | Internet | RAM |
|-------------|----------------------|---------|----------|-----|
| gTTS (défaut) | `gtts` | Bonne | Oui | Faible |
| Coqui TTS | `coqui` | Excellente | Non | 2-4 Go |

Pour changer : `TTS_MODEL=coqui` dans `.env` + `pip install TTS`
