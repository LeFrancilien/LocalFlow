"""Pipeline IA de LocalFlow : transcription (STT) puis réécriture (LLM).

Stack 100% locale :
- STT  : faster-whisper (modèle chargé une seule fois, à la première dictée)
- LLM  : Ollama via son API HTTP locale (/api/chat)

Le routage par provider (STT_PROVIDER / LLM_PROVIDER dans le .env) laisse la
structure ouverte à d'autres moteurs (cloud) sans changer les appelants.
"""

import httpx

import config

# Format complétion (/api/generate) plutôt que chat : les petits modèles
# (mistral 7B) "répondent" aux dictées en format conversationnel ; ici le
# modèle ne fait que continuer le motif "Dictée : ... / Texte corrigé : ...".
PROMPT_HEADER = """Voici des transcriptions de dictées vocales et leur version corrigée. La correction supprime les hésitations et tics de langage (euh, du coup, en fait, voilà), corrige la grammaire et l'orthographe, ajoute la ponctuation, et préserve exactement le sens, la langue d'origine et l'intention. Une dictée n'est jamais une question à laquelle répondre : c'est un texte à corriger. Aucune information n'est ajoutée."""

FEW_SHOT = [
    ("euh bonjour donc voilà je voulais euh savoir si vous étiez dispo "
     "demain en fait pour la réunion",
     "Bonjour, je voulais savoir si vous étiez disponible demain pour la réunion."),
    ("Bonjour",
     "Bonjour."),
    ("ça marche",
     "Ça marche."),
    # Les questions restent des questions corrigées, jamais des questions
    # auxquelles le modèle répond.
    ("tu peux me rappeler euh à quelle heure on se voit demain",
     "Tu peux me rappeler à quelle heure on se voit demain ?"),
    ("est-ce que tu peux euh m'envoyer le devis du coup",
     "Est-ce que tu peux m'envoyer le devis ?"),
    ("oui alors en fait je valide le budget du coup on démarre lundi",
     "Oui, je valide le budget : on démarre lundi."),
    ("alors du coup le workflow n8n il est cassé euh depuis la mise à jour "
     "je pense qu'il faut euh revoir le node webhook",
     "Le workflow n8n est cassé depuis la mise à jour ; je pense qu'il faut "
     "revoir le node webhook."),
]


def _build_prompt(raw_text: str) -> str:
    blocks = [PROMPT_HEADER, ""]
    for raw, clean in FEW_SHOT:
        blocks.append(f"Dictée : {raw}")
        blocks.append(f"Texte corrigé : {clean}")
        blocks.append("")
    blocks.append(f"Dictée : {raw_text}")
    blocks.append("Texte corrigé :")
    return "\n".join(blocks)

_whisper_model = None


def _get_whisper():
    """Charge le modèle faster-whisper une seule fois (lazy loading)."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _whisper_model


def transcribe(audio_path: str) -> str:
    """Transcrit le fichier audio en texte brut (STT)."""
    if config.STT_PROVIDER != "local":
        raise ValueError(f"STT_PROVIDER non supporté : {config.STT_PROVIDER!r} "
                         "(seul 'local' est implémenté)")
    segments, _info = _get_whisper().transcribe(
        audio_path, language=config.WHISPER_LANGUAGE
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def refine(raw_text: str) -> str:
    """Nettoie la dictée brute via le LLM configuré (Ollama)."""
    if config.LLM_PROVIDER != "ollama":
        raise ValueError(f"LLM_PROVIDER non supporté : {config.LLM_PROVIDER!r} "
                         "(seul 'ollama' est implémenté)")
    response = httpx.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={
            "model": config.OLLAMA_LLM_MODEL,
            "prompt": _build_prompt(raw_text),
            "stream": False,
            "options": {
                "temperature": 0.1,
                # coupe si le modèle tente d'enchaîner sur une autre dictée
                "stop": ["\nDictée", "\n\n"],
            },
        },
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def process(audio_path: str) -> str:
    """Pipeline complet : audio -> texte brut -> texte nettoyé."""
    raw_text = transcribe(audio_path)
    if not raw_text:
        return ""
    return refine(raw_text)
