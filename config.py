"""Chargement et validation des variables d'environnement.

Complété au fil des phases : pour l'instant, seuls les paramètres audio
sont exposés (Phase 2). Les paramètres IA et raccourcis arrivent ensuite.
"""

from pathlib import Path

from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# --- Audio (F2) ---
AUDIO_TEMP_FILE = str(PROJECT_ROOT / os.getenv("AUDIO_TEMP_FILE", "temp_speech.wav"))
SAMPLE_RATE = 16000  # 16 kHz mono 16-bit PCM : format recommandé pour Whisper
CHANNELS = 1
AUDIO_DEVICE_KEYWORDS = [
    k.strip() for k in os.getenv("AUDIO_DEVICE_KEYWORDS", "").split(",") if k.strip()
]

# --- Raccourci clavier global (F1) ---
GLOBAL_HOTKEY = os.getenv("GLOBAL_HOTKEY", "f9")

# --- Pipeline IA (F3) ---
STT_PROVIDER = os.getenv("STT_PROVIDER", "local")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# STT local : faster-whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE") or None  # None = auto-détection

# LLM local : Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "mistral")
