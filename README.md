# LocalFlow

Assistant de dictée vocale local, gratuit et privé — clone personnel de Wispr Flow.
Appuie sur **F9** n'importe où dans Windows : parle, réappuie sur F9, et le texte
corrigé s'insère au curseur actif. 100 % local : aucune donnée ne quitte le PC.

**Statut : terminé et validé** (2026-07-05). Démarre automatiquement avec Windows.

## Utilisation quotidienne

1. LocalFlow démarre tout seul avec Windows (silencieux, aucune fenêtre).
2. Place le curseur dans n'importe quel champ de texte (mail, navigateur, IDE...).
3. **F9** → bulle rouge "🎙️ Écoute..." en bas à droite → dicte.
4. **F9** à nouveau → bulle bleue "⚙️ Traitement..." → flash vert → texte inséré.

La première dictée après un démarrage est plus lente (chargement du modèle
Whisper en mémoire). Les suivantes sont rapides.

## Architecture

```
F9 (pynput GlobalHotKeys)
  → audio_recorder.py   micro → temp_speech.wav (16 kHz mono, format Whisper)
  → ai_pipeline.py      STT faster-whisper → nettoyage LLM Ollama (mistral)
  → text_injector.py    presse-papiers sauvegardé → Ctrl+V → restauré
  → ui_overlay.py       bulle de statut Tkinter (bas droite, topmost)
```

| Fichier | Rôle |
|---|---|
| `main.py` | Boucle principale : hotkey en thread de fond, mainloop Tk en thread principal |
| `config.py` | Charge le `.env` (hotkey, modèles, providers) |
| `audio_recorder.py` | Capture micro → WAV temporaire |
| `ai_pipeline.py` | Transcription + réécriture LLM |
| `text_injector.py` | "Smart Paste" sans perdre le presse-papiers |
| `ui_overlay.py` | Overlay d'état (IDLE caché / RECORDING / PROCESSING / SUCCESS / ERROR) |
| `test_*.py` | Tests unitaires des modules |

Stack : Python (venv local), faster-whisper (STT), Ollama + mistral (LLM),
pynput (hotkey + collage), Tkinter (overlay). Config dans `.env`
(`GLOBAL_HOTKEY=f9`, `STT_PROVIDER=local`, `LLM_PROVIDER=ollama`).

## Démarrage automatique

- `LocalFlow.vbs` dans le dossier Démarrage :
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
- Il lance `venv\Scripts\pythonw.exe main.py` (pythonw = sans console).
  Deux processus `pythonw.exe` au Gestionnaire des tâches, c'est normal
  (lanceur du venv + appli).
- Ollama a son propre démarrage auto dans le même dossier (`Ollama.lnk`).
- **Désactiver** : Gestionnaire des tâches → "Applications de démarrage",
  ou supprimer le `.vbs`. **Arrêter la session en cours** : fin de tâche
  sur `pythonw.exe`.

## Lancement manuel (debug)

```powershell
cd C:\Users\user\iCloudDrive\oakflow-wiki\projects\LocalFlow
.\venv\Scripts\python.exe main.py
```

Affiche les logs ([RECORDING], [PROCESSING], [SUCCESS], [ERROR]) dans la
console.

## Fichier de log

Toute l'activité (y compris en mode silencieux) est écrite dans
`localflow.log` à la racine du projet : démarrage, dictées, textes injectés,
erreurs avec stacktrace. Rotation automatique à 1 Mo (1 fichier de backup
`localflow.log.1`). C'est le premier réflexe si F9 semble mort ou si une
dictée échoue sans explication.

## Décisions techniques (le pourquoi)

- **Prompt LLM en format complétion, pas chat** (`/api/generate`) : mistral 7B
  en format chat "répondait" aux dictées courtes ("quel est ton prénom" →
  "Mon prénom est Nettoyeur") ou paraphrasait ses instructions. Le motif
  `Dictée : … / Texte corrigé : …` avec 8 exemples few-shot (dont mono-mots et
  questions) + paramètre `stop` a éliminé le problème. Limite résiduelle 7B :
  micro-fautes occasionnelles ("Peut-tu"). Si gênant → changer
  `OLLAMA_LLM_MODEL` pour `llama3.1` ou `qwen2.5` dans le `.env`.
- **Tkinter dans le thread principal** : obligatoire. Le listener hotkey tourne
  en thread de fond ; les threads signalent l'overlay via une queue vidée
  toutes les 100 ms (`set_state()` est thread-safe).
- **pynput 1.8.2 ignore les touches injectées** dans `GlobalHotKeys`
  (`if not injected`). Impossible donc de tester F9 en simulant la touche par
  logiciel — seul un appui physique déclenche.
- **Le venv a un pip cassé** (probablement corrompu par la sync iCloud).
  Si une dépendance manque un jour : recréer le venv
  (`python -m venv venv` + `pip install -r requirements.txt`).
- **iCloud Drive bloque parfois suppressions/déplacements** ("fournisseur de
  synchronisation cloud") : si un fichier refuse d'être supprimé en ligne de
  commande, passer par l'Explorateur Windows.

## Dépannage rapide

| Symptôme | Cause probable | Solution |
|---|---|---|
| F9 ne fait rien | Appli pas lancée | Consulter `localflow.log` ; vérifier `pythonw.exe` au Gestionnaire des tâches |
| Erreur au traitement (bulle rouge) | Ollama pas démarré | Vérifier qu'Ollama tourne (`ollama list`) |
| Texte bizarre / méta-commentaires | Régression prompt | Voir "Décisions techniques" ; tester `refine()` directement |
| Rien ne s'insère mais flash vert | Curseur pas dans un champ texte | Cliquer dans un champ avant F9 |
| `temp_speech.wav` traîne dans le dossier | Normal | Fichier de travail, nettoyé après chaque dictée |
