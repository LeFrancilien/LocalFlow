"""Test isolé du module audio_recorder (Phase 2).

Enregistre quelques secondes depuis le micro par défaut, puis vérifie que
le WAV produit est lisible, au bon format, et contient du signal.
Lancer :  venv/Scripts/python.exe test_audio_recorder.py [durée_en_secondes]
"""

import sys
import time

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from audio_recorder import AudioRecorder

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0

recorder = AudioRecorder()
if recorder.device is not None:
    print(f"Micro sélectionné (via AUDIO_DEVICE_KEYWORDS) : "
          f"{sd.query_devices(recorder.device)['name']}")
else:
    print(f"Micro par défaut : {sd.query_devices(kind='input')['name']}")

print(f"Enregistrement de {DURATION:.0f}s — parlez maintenant !")
recorder.start()
time.sleep(DURATION)
path = recorder.stop()

if path is None:
    print("ECHEC : aucun audio capturé.")
    sys.exit(1)

rate, data = wavfile.read(path)
duration = len(data) / rate
peak = int(np.abs(data).max())
print(f"Fichier : {path}")
print(f"Format  : {rate} Hz, {data.dtype}, {data.ndim} canal(aux)")
print(f"Durée   : {duration:.2f}s — Pic d'amplitude : {peak} / 32767")

ok = rate == 16000 and data.dtype == np.int16 and duration >= DURATION * 0.8
if peak < 100:
    print("ATTENTION : signal quasi nul — le micro n'a probablement rien capté.")
elif ok:
    print("SUCCES : le WAV est propre et contient du signal.")
else:
    print("ECHEC : format ou durée inattendus.")
    sys.exit(1)
