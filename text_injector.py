"""Injection "Smart Paste" du texte au curseur actif (F4).

1. Sauvegarde le contenu actuel du presse-papiers.
2. Y place le texte nettoyé.
3. Simule Ctrl+V (Cmd+V sur macOS).
4. Micro-délai pour laisser le système coller.
5. Restaure le presse-papiers d'origine.
"""

import platform
import time

import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()

CLIPBOARD_SET_DELAY = 0.05  # laisse le presse-papiers se mettre à jour
PASTE_DELAY = 0.1           # laisse l'application active coller le texte


def inject_text(text: str) -> None:
    """Colle `text` à l'emplacement du curseur actif sans perturber
    le presse-papiers de l'utilisateur."""
    if not text:
        return

    original = None
    try:
        original = pyperclip.paste()
    except pyperclip.PyperclipException:
        pass  # presse-papiers illisible (contenu non-texte) : rien à restaurer

    pyperclip.copy(text)
    time.sleep(CLIPBOARD_SET_DELAY)

    modifier = Key.cmd if platform.system() == "Darwin" else Key.ctrl
    with _keyboard.pressed(modifier):
        _keyboard.press("v")
        _keyboard.release("v")

    time.sleep(PASTE_DELAY)

    if original is not None:
        pyperclip.copy(original)
