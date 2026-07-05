"""Point d'entrée de LocalFlow — boucle principale.

Un premier appui sur le raccourci global (GLOBAL_HOTKEY dans le .env) lance
l'enregistrement ; un second appui l'arrête, puis le pipeline IA transcrit,
nettoie et injecte le texte au curseur actif. Ctrl+C pour quitter.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pynput import keyboard

import ai_pipeline
import config
import text_injector
import ui_overlay
from audio_recorder import AudioRecorder

LOG_FILE = Path(__file__).parent / "localflow.log"


def setup_logging():
    """Console + fichier. Sous pythonw (mode silencieux, stdout absent),
    le fichier est le seul moyen de voir ce qui se passe."""
    handlers = [
        RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=1, encoding="utf-8"
        )
    ]
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def normalize_hotkey(raw: str) -> str:
    """Convertit la valeur du .env en syntaxe pynput.

    Les touches nommées (f9, space, esc...) doivent être entre chevrons ;
    on accepte donc "f9" aussi bien que "<f9>" ou "<ctrl>+<shift>+e".
    """
    parts = []
    for token in raw.split("+"):
        token = token.strip()
        if len(token) > 1 and not token.startswith("<"):
            token = f"<{token}>"
        parts.append(token)
    return "+".join(parts)


class LocalFlowApp:
    def __init__(self, overlay: ui_overlay.StatusOverlay):
        self.recorder = AudioRecorder()
        self.overlay = overlay
        self._busy = False

    def on_hotkey(self):
        """Bascule enregistrement : 1er appui = démarre, 2e appui = arrête
        et lance le pipeline (transcription -> nettoyage -> injection)."""
        if self._busy:
            logging.info("[BUSY] Traitement en cours, réessayez dans un instant.")
            return
        if not self.recorder.is_recording:
            logging.info("[RECORDING] Enregistrement en cours... (réappuyez pour arrêter)")
            self.overlay.set_state(ui_overlay.RECORDING)
            self.recorder.start()
        else:
            path = self.recorder.stop()
            if path is None:
                logging.error("[ERROR] Aucun audio capturé.")
                self.overlay.set_state(ui_overlay.ERROR)
                return
            self._busy = True
            # Thread séparé : le callback pynput ne doit pas bloquer plusieurs
            # secondes, sinon le raccourci devient inerte pendant le traitement.
            threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, audio_path: str):
        logging.info("[PROCESSING] Transcription et nettoyage en cours...")
        self.overlay.set_state(ui_overlay.PROCESSING)
        try:
            text = ai_pipeline.process(audio_path)
            if text:
                text_injector.inject_text(text)
                logging.info(f"[SUCCESS] Texte injecté : {text}")
                self.overlay.set_state(ui_overlay.SUCCESS)
            else:
                logging.error("[ERROR] Transcription vide, rien à injecter.")
                self.overlay.set_state(ui_overlay.ERROR)
        except Exception:
            logging.exception("[ERROR] Pipeline")
            self.overlay.set_state(ui_overlay.ERROR)
        finally:
            self.recorder.cleanup()
            self._busy = False


def main():
    setup_logging()
    try:
        hotkey = normalize_hotkey(config.GLOBAL_HOTKEY)
        # Tkinter doit tourner dans le thread principal : le listener hotkey
        # passe en arrière-plan et la mainloop de l'overlay prend le relais.
        overlay = ui_overlay.StatusOverlay()
        app = LocalFlowApp(overlay)
        listener = keyboard.GlobalHotKeys({hotkey: app.on_hotkey})
        listener.start()
        logging.info(f"LocalFlow démarré — raccourci global : {config.GLOBAL_HOTKEY}")
        try:
            overlay.run()
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
    except Exception:
        # Sous pythonw, une exception au démarrage serait invisible sans ça.
        logging.exception("Erreur fatale au démarrage")
        raise


if __name__ == "__main__":
    main()
