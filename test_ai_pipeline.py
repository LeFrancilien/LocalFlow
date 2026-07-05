"""Test isolé du pipeline IA (Phase 4).

Transcrit un WAV existant puis le fait nettoyer par Ollama, en affichant
les deux sorties pour comparaison.
Lancer :  venv/Scripts/python.exe test_ai_pipeline.py [chemin_du_wav]
"""

import sys
import time

import ai_pipeline
import config

audio_path = sys.argv[1] if len(sys.argv) > 1 else config.AUDIO_TEMP_FILE

print(f"Whisper : {config.WHISPER_MODEL} ({config.WHISPER_DEVICE}/"
      f"{config.WHISPER_COMPUTE_TYPE}) — LLM : {config.OLLAMA_LLM_MODEL}")
print(f"Audio   : {audio_path}\n")

t0 = time.perf_counter()
raw = ai_pipeline.transcribe(audio_path)
t1 = time.perf_counter()
print(f"--- Transcription brute ({t1 - t0:.1f}s, chargement modèle inclus) ---")
print(raw or "(vide)")

if not raw:
    print("ECHEC : transcription vide.")
    sys.exit(1)

t2 = time.perf_counter()
clean = ai_pipeline.refine(raw)
t3 = time.perf_counter()
print(f"\n--- Texte nettoyé par le LLM ({t3 - t2:.1f}s) ---")
print(clean or "(vide)")

print("\nSUCCES" if clean else "\nECHEC : réponse LLM vide.")
