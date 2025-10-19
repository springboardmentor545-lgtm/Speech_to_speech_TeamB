import azure.cognitiveservices.speech as speechsdk
import os

# Replace with your actual values or set them as environment variables
SPEECH_KEY = "YOUR_SPEECH_KEY"
SERVICE_REGION = "YOUR_REGION"

# Setup
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY , region=SERVICE_REGION)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# Define absolute path to transcripts folder
output_path = r"transcripts\recognized_output.txt"

print("Say something...")
result = recognizer.recognize_once_async().get()

# Handle result
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(result.text)
elif result.reason == speechsdk.ResultReason.NoMatch:
    print("No speech could be recognized.")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print("Speech Recognition canceled:", cancellation_details.reason)
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print("Error details:", cancellation_details.error_details)
