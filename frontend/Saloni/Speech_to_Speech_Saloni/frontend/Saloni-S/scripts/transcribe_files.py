# transcribe_files.py
import os, csv
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

INPUT_DIR = "../samples/input"
OUT_CSV = "../samples/output/transcripts.csv"
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

def transcribe_file(path, language="en-US"):
    speech_config.speech_recognition_language = language
    audio = speechsdk.AudioConfig(filename=path)
    rec = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio)
    res = rec.recognize_once_async().get()
    if res.reason == speechsdk.ResultReason.RecognizedSpeech:
        return res.text
    return ""

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["filename","language","transcript"])
    for fn in os.listdir(INPUT_DIR):
        if fn.lower().endswith(".wav"):
            lang = "hi-IN" if fn.startswith("hi_") else "en-US"
            text = transcribe_file(os.path.join(INPUT_DIR, fn), lang)
            w.writerow([fn, lang, text])
            print("Done:", fn, "→", text[:80])
print("Saved CSV:", OUT_CSV)
