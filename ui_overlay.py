"""Overlay Tkinter de statut (F5) : bulle flottante en bas à droite de l'écran.

Tkinter exige de tourner dans le thread principal ; les autres threads
(hotkey pynput, pipeline IA) signalent leurs changements d'état via
`set_state()`, thread-safe grâce à une queue vidée toutes les 100 ms.
"""

import queue
import tkinter as tk

IDLE = "IDLE"
RECORDING = "RECORDING"
PROCESSING = "PROCESSING"
SUCCESS = "SUCCESS"
ERROR = "ERROR"

# state -> (texte, couleur de fond)
_STYLES = {
    RECORDING: ("🎙️ Écoute...", "#C62828"),
    PROCESSING: ("⚙️ Traitement en cours...", "#1565C0"),
    SUCCESS: ("✔ Texte injecté", "#2E7D32"),
    ERROR: ("✖ Erreur", "#B71C1C"),
}

FLASH_DURATION_MS = 1500  # durée d'affichage de SUCCESS / ERROR
POLL_INTERVAL_MS = 100
MARGIN = 40  # distance du coin bas-droit de l'écran


class StatusOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # pas de barre de titre
        self.root.attributes("-topmost", True)
        self.label = tk.Label(
            self.root,
            font=("Segoe UI", 11),
            fg="white",
            padx=14,
            pady=6,
        )
        self.label.pack()
        self._queue = queue.Queue()
        self._flash_job = None
        self.root.withdraw()  # IDLE au démarrage
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def set_state(self, state: str) -> None:
        """Appelable depuis n'importe quel thread."""
        self._queue.put(state)

    def run(self) -> None:
        """Boucle Tkinter — bloque le thread principal."""
        self.root.mainloop()

    def stop(self) -> None:
        self.root.after(0, self.root.destroy)

    def _poll(self):
        try:
            while True:
                self._apply(self._queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _apply(self, state: str):
        if self._flash_job is not None:
            self.root.after_cancel(self._flash_job)
            self._flash_job = None
        if state == IDLE or state not in _STYLES:
            self.root.withdraw()
            return
        text, color = _STYLES[state]
        self.label.config(text=text, bg=color)
        self.root.config(bg=color)
        self._place_bottom_right()
        self.root.deiconify()
        if state in (SUCCESS, ERROR):
            self._flash_job = self.root.after(
                FLASH_DURATION_MS, lambda: self._apply(IDLE)
            )

    def _place_bottom_right(self):
        self.root.update_idletasks()  # recalcule la taille selon le texte
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        x = self.root.winfo_screenwidth() - w - MARGIN
        y = self.root.winfo_screenheight() - h - MARGIN
        self.root.geometry(f"+{x}+{y}")
