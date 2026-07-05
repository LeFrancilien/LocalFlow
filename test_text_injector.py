"""Test isolé du Smart Paste (Phase 5).

Laisse 5 secondes pour placer le curseur dans un champ texte (bloc-notes...),
injecte une phrase de test, puis vérifie que le presse-papiers d'origine
a bien été restauré.
Lancer :  venv/Scripts/python.exe test_text_injector.py
"""

import time

import pyperclip

from text_injector import inject_text

SENTINEL = "contenu-original-du-presse-papiers"
pyperclip.copy(SENTINEL)

print("Placez votre curseur dans un champ texte (bloc-notes)... 5 secondes.")
time.sleep(5)

inject_text("Injection LocalFlow réussie : le Smart Paste fonctionne.")
time.sleep(0.3)

restored = pyperclip.paste()
print(f"Presse-papiers restauré : {'OUI' if restored == SENTINEL else 'NON — ' + repr(restored)}")
print("Vérifiez que la phrase de test est apparue à l'emplacement du curseur.")
