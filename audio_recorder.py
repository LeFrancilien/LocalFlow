"""Capture du microphone par défaut et enregistrement en WAV temporaire.

Format : 16000 Hz, mono, 16-bit PCM (compatibilité maximale avec Whisper).
Usage :
    recorder = AudioRecorder()
    recorder.start()
    ...
    path = recorder.stop()   # écrit le WAV et retourne son chemin
"""

import os

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

import config


def find_input_device(keywords: list[str]) -> int | None:
    """Retourne l'index du premier périphérique d'entrée dont le nom contient
    un des mots-clés (insensible à la casse). None si aucun ne correspond."""
    for index, device in enumerate(sd.query_devices()):
        if device["max_input_channels"] > 0 and any(
            k.lower() in device["name"].lower() for k in keywords
        ):
            return index
    return None


class AudioRecorder:
    def __init__(self, output_file: str = config.AUDIO_TEMP_FILE,
                 sample_rate: int = config.SAMPLE_RATE,
                 device: int | None = None):
        self.output_file = output_file
        self.sample_rate = sample_rate
        # Périphérique explicite > mots-clés du .env > micro par défaut
        if device is None and config.AUDIO_DEVICE_KEYWORDS:
            device = find_input_device(config.AUDIO_DEVICE_KEYWORDS)
        self.device = device
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        """Ouvre le micro par défaut du système et commence la capture."""
        if self.is_recording:
            return
        self._chunks = []
        self._stream = sd.InputStream(
            device=self.device,
            samplerate=self.sample_rate,
            channels=config.CHANNELS,
            dtype="int16",
            callback=self._on_audio,
        )
        self._stream.start()

    def _on_audio(self, indata: np.ndarray, frames, time_info, status) -> None:
        self._chunks.append(indata.copy())

    def stop(self) -> str | None:
        """Arrête la capture, écrit le WAV et retourne son chemin.

        Retourne None si rien n'a été capturé.
        """
        if not self.is_recording:
            return None
        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._chunks:
            return None

        audio = np.concatenate(self._chunks)
        self._chunks = []
        wavfile.write(self.output_file, self.sample_rate, audio)
        return self.output_file

    def cleanup(self) -> None:
        """Supprime le fichier temporaire après traitement (F2)."""
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
