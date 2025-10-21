import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Azure credentials from environment variables
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

# Setup
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY , region=SERVICE_REGION)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# Define path to transcripts folder (relative to script location)
output_dir = os.path.join(os.path.dirname(__file__), "..", "transcripts")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "recognized_output.txt")

print("Say something...")
result = recognizer.recognize_once_async().get()

# Handle result
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(result.text)
    print(f"Transcription saved to: {os.path.abspath(output_path)}")
elif result.reason == speechsdk.ResultReason.NoMatch:
    print("No speech could be recognized.")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print("Speech Recognition canceled:", cancellation_details.reason)
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print("Error details:", cancellation_details.error_details)
