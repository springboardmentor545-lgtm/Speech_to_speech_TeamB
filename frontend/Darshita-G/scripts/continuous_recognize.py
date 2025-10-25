import os
import time
import csv
from datetime import datetime
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# Load environment variables from .env file
load_dotenv()

# Get Azure credentials from environment variables
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

if not SPEECH_KEY or not SERVICE_REGION:
    raise ValueError("Please set SPEECH_KEY and SERVICE_REGION in .env file")

# Configure speech recognition
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

def stop_cb(evt):
    print('CLOSING on {}'.format(evt))
    recognizer.stop_continuous_recognition()

def save_to_csv(text):
    """Save the recognized text to a CSV file."""
    try:
        # Ensure the transcripts directory exists
        transcripts_dir = os.path.join(os.path.dirname(__file__), '..', 'transcripts')
        os.makedirs(transcripts_dir, exist_ok=True)
        
        csv_path = os.path.join(transcripts_dir, 'continuous_transcripts.csv')
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_path)
        
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write headers if file is being created
            if not file_exists:
                writer.writerow(['S.no', 'Timestamp', 'Transcript'])
            
            # Get current row count to generate S.no
            row_count = 0
            if file_exists:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for _ in f) - 1  # Subtract 1 for header
                    row_count = max(0, row_count)  # Ensure non-negative
            
            # Write the data
            writer.writerow([
                row_count + 1,  # S.no
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Timestamp
                text.strip()  # Transcript
            ])
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def recognized_cb(evt):
    """Callback for recognized speech events."""
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        recognized_text = evt.result.text
        print(f"RECOGNIZED: {recognized_text}")
        
        # Save to CSV
        save_to_csv(recognized_text)

recognizer.recognized.connect(recognized_cb)
recognizer.canceled.connect(lambda evt: print("CANCELED: {}".format(evt)))
recognizer.session_stopped.connect(stop_cb)
print("Starting continuous recognition...")
try:
    recognizer.start_continuous_recognition()
    print("Listening... press Ctrl+C to stop.")
    
    # Keep the main thread alive
    while True:
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nStopping recognition...")
    try:
        recognizer.stop_continuous_recognition()
    except Exception as e:
        print(f"Error during stop: {e}")
    print("Recognition stopped.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    print("Exiting...")