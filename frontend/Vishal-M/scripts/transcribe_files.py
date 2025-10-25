import os
import csv
import time
import azure.cognitiveservices.speech as speechsdk

# Load credentials from environment variables for security
# Create a .env file in the same directory (and add it to .gitignore!)
# .env file content:
# SPEECH_KEY="your_actual_azure_speech_key"
# SERVICE_REGION="your_actual_azure_region"
from dotenv import load_dotenv
load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

INPUT_DIR = r"E:\Speech_to_speech_TeamB\frontend\Vishal-M\speech_samples" # Consider making this a script argument
OUTPUT_CSV = r"E:\Speech_to_speech_TeamB\frontend\Vishal-M\transcripts\transcripts_recognize_once.csv"

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
out_dir = os.path.dirname(OUTPUT_CSV)
os.makedirs(out_dir, exist_ok=True)

print("Starting batch transcription...\n")

def open_output_csv(path):
    try:
        return open(path, mode='w', newline='', encoding='utf-8')
    except PermissionError as e:
        # Fallback to writing in the current working directory with a timestamped name
        fallback = os.path.join(os.getcwd(), f"transcripts_fallback_{int(time.time())}.csv")
        print(f"Warning: cannot write to {path}: {e}. Falling back to {fallback}")
        return open(fallback, mode='w', newline='', encoding='utf-8')

with open_output_csv(OUTPUT_CSV) as csvfile:
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
