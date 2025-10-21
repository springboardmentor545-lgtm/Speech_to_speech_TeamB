import os
import csv
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Azure credentials from environment variables
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")


# Paths (relative to script location)
INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "speech_samples")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "transcripts")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transcripts.csv")

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

def transcribe_file(file_path, language="en-US"):
    """Transcribe a single audio file"""
    speech_config.speech_recognition_language = language
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "[No speech recognized]"
    elif result.reason == speechsdk.ResultReason.Canceled:
        return f"[Error: {result.cancellation_details.reason}]"
    else:
        return "[Unknown error]"

# Create transcripts directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Starting batch transcription...\n")

with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "language", "transcript"])
    # Recursively walk through all subfolders and files within INPUT_DIR
    for root, dirs, files in os.walk(INPUT_DIR):
        for fname in sorted(files):
            if not fname.lower().endswith(".wav"):
                continue
            
            # Detect language from filename
            if fname.startswith("en_"):
                lang_code = "en-US"
                lang = "en"
            elif fname.startswith("hi_"):
                lang_code = "hi-IN"
                lang = "hi"
            else:
                lang_code = "en-US"
                lang = "unknown"
            
            file_path = os.path.join(root, fname)
            print(f"Transcribing: {file_path} ({lang})...")
            
            text = transcribe_file(file_path, lang_code)
            writer.writerow([fname, lang, text])
            print(f"  → {text}\n")

print(f"✓ Transcription complete! Results saved to: {OUTPUT_CSV}")
