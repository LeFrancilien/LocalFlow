# LocalFlow

[Français](README.fr.md)

A local, free, privacy-first dictation tool for Windows. Press a global hotkey, speak, press it again, and the corrected text is inserted at your cursor, in any application. With the default settings, audio and text never leave your machine.

It is a personal project in an early stage: one author, working on Windows 11 only. It is inspired by cloud dictation tools such as Wispr Flow, but it runs entirely on local models and has no running cost.

## How it works

1. Press **F9** anywhere. A red overlay shows "Listening...".
2. Speak, then press **F9** again. A blue overlay shows "Processing...".
3. [faster-whisper](https://github.com/SYSTRAN/faster-whisper) transcribes the audio.
4. A local LLM served by [Ollama](https://ollama.com) (Mistral by default) removes filler words and fixes grammar and punctuation.
5. The text is pasted at the active cursor. Your clipboard content is saved before the paste and restored after it.

```
F9 (pynput GlobalHotKeys)
  -> audio_recorder.py   microphone -> temp_speech.wav (16 kHz, mono)
  -> ai_pipeline.py      faster-whisper STT -> Ollama cleanup
  -> text_injector.py    save clipboard -> Ctrl+V -> restore clipboard
  -> ui_overlay.py       Tkinter status bubble (bottom right, always on top)
```

| File | Role |
|---|---|
| `main.py` | Main loop: hotkey listener in a background thread, Tk mainloop in the main thread |
| `config.py` | Reads settings from `.env` |
| `audio_recorder.py` | Records the microphone to a temporary WAV file |
| `ai_pipeline.py` | Transcription and LLM rewrite |
| `text_injector.py` | "Smart paste" that preserves the clipboard |
| `ui_overlay.py` | Status overlay (idle, recording, processing, success, error) |
| `test_*.py` | Manual check scripts for each module (not an automated test suite yet) |

## Requirements

- Windows (developed and used on Windows 11, not tested elsewhere)
- Python 3 (developed with 3.14, no other version tested)
- [Ollama](https://ollama.com) running locally, with a model pulled: `ollama pull mistral`
- A microphone

## Install

```powershell
git clone https://github.com/LeFrancilien/LocalFlow.git
cd LocalFlow
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install faster-whisper
```

`faster-whisper` is imported by `ai_pipeline.py` but is not listed in `requirements.txt` yet, so it is installed separately for now.

Create a `.env` file at the project root if you want to change a default (all keys are optional):

| Key | Default | Meaning |
|---|---|---|
| `GLOBAL_HOTKEY` | `f9` | Hotkey that starts and stops dictation |
| `WHISPER_MODEL` | `small` | faster-whisper model size |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | Quantization used by faster-whisper |
| `WHISPER_LANGUAGE` | empty | Language code, empty means auto-detect |
| `OLLAMA_HOST` | `http://localhost:11434` | Address of the Ollama server |
| `OLLAMA_LLM_MODEL` | `mistral` | Model used for the cleanup step |
| `AUDIO_DEVICE_KEYWORDS` | empty | Comma-separated keywords to pick the microphone by name |

## Run

```powershell
.\venv\Scripts\python.exe main.py
```

Logs appear in the console. Use `pythonw.exe` instead of `python.exe` to run without a console window, for example from a script in your Windows Startup folder. All activity (start-up, dictations, errors with stack traces) is also written to `localflow.log` in the project folder, rotated at 1 MB.

The first dictation after start-up is slower because the Whisper model is loaded into memory. Later ones are faster.

## Design notes

- **Completion-style prompt, not chat.** With the chat format, Mistral 7B often answered short dictations instead of cleaning them (asked "what is your first name", it replied with a name). The cleanup call uses Ollama's `/api/generate` endpoint with a `Dictation: ... / Corrected text: ...` pattern, eight few-shot examples (including single words and questions) and a `stop` parameter. That removed the problem. A residual limit of the 7B model is the occasional small typo. If it bothers you, set `OLLAMA_LLM_MODEL` to `llama3.1` or `qwen2.5`.
- **Tkinter runs in the main thread.** The hotkey listener runs in a background thread and signals the overlay through a queue drained every 100 ms.
- **pynput ignores injected key events** in `GlobalHotKeys`, so F9 cannot be tested by simulating the key. Only a physical key press triggers it.

## Known limitations

- Windows only. Text insertion relies on the clipboard and Ctrl+V.
- Only the local providers are implemented: faster-whisper for speech-to-text and Ollama for the LLM. `STT_PROVIDER` and `LLM_PROVIDER` exist in `config.py`, but other values are not supported.
- `requirements.txt` lists packages the current pipeline does not use (`openai`, `anthropic`) and misses `faster-whisper`.
- No automated tests, no CI, no installer.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| F9 does nothing | App not running | Check `localflow.log`, and look for `pythonw.exe` in Task Manager |
| Red error bubble after processing | Ollama is not running | Start Ollama and check `ollama list` |
| Odd text or meta-comments in the output | Prompt regression | See "Design notes", and call `refine()` directly to test |
| Green flash but nothing is inserted | The cursor is not in a text field | Click into a text field before pressing F9 |
| `temp_speech.wav` is left in the folder | Normal | Working file, cleaned after each dictation |

## License

[MIT](LICENSE)
