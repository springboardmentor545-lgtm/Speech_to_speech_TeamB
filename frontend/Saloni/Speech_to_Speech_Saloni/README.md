# Speech-to-Speech Translator (Streamlit GUI)

## Quick Start
1. Create and activate a Python 3.10+ venv
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill Azure keys
4. Run the GUI: `streamlit run app.py`

## What it does
- Mic → Speech-to-Text (Azure STT)
- Translate (Azure Translator)
- Text-to-Speech (Azure TTS)
- Plays translated audio in the browser

## Structure
```
.
├── .env
├── requirements.txt
├── app.py
└── frontend/Saloni-S/
    ├── README.md
    ├── samples/
    │   ├── input/
    │   └── output/
    └── scripts/
        ├── recognize_once.py
        ├── transcribe_files.py
        ├── translate_text.py
        ├── text_to_speech.py
        ├── main_pipeline.py
        └── batch_s2s.py
```
