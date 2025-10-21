# Initial Setup (One-Time Only)

## 1. Create Virtual Environment
```In terminal:
python -m venv venv
```

## 2. Activate Virtual Environment
```In terminal:
venv\Scripts\Activate
```

## 3. Install Dependencies
```In terminal:
pip install -r requirements.txt
```

## 4. Install ffmpeg (Optional - for audio conversion)
```In terminal:
choco install ffmpeg
```

## 5. Verify .env File Exists
Check that `.env` file has:
```
SPEECH_KEY=key_here
SERVICE_REGION=centralindia
```

## 6. Test the Setup
```In terminal:
cd frontend\Vishal-M\scripts
python recognize_once.py
```

Speak into microphone to verify it works.

---

**Done! Now use DAILY_SETUP.md every time you open the project.**
