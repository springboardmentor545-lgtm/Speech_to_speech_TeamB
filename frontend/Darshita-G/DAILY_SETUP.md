# Daily Setup (Every Time You Open Project)

## 1. Activate Virtual Environment
```In terminal:
venv\Scripts\Activate
```

## 2. Navigate to Scripts Folder
```In terminal:
cd frontend\Vishal-M\scripts
```

## 3. Run Scripts

### Real-time Recognition:
```In terminal:
python recognize_once.py
```

### Batch Transcription:
```In terminal:
python transcribe_files.py
```

---

## Audio Conversion (if needed)
```In terminal:
ffmpeg -i input.m4a -ac 1 -ar 16000 output.wav
```

---

## Troubleshooting

**"python not recognized"**: Activate venv first  
**"No module named 'azure'"**: Run `pip install -r requirements.txt`  
**"Authentication failed"**: Check `.env` file exists in project root
