import azure.cognitiveservices.speech as speechsdk
import os

SPEECH_KEY = "YOUR_SPEECH_KEY"
SERVICE_REGION = "YOUR_REGION"

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
speech_config.speech_recognition_language = "en-US"
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

print("Continuous Speech Recognition Started...")
print("Speak into your microphone. Press Ctrl+C to stop.\n")

def recognized_cb(evt):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"RECOGNIZED: {evt.result.text}")
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print("NOMATCH: Speech could not be recognized")

def stop_cb(evt):
    print(f'\nSESSION STOPPED: {evt}')
    recognizer.stop_continuous_recognition()

recognizer.recognized.connect(recognized_cb)
recognizer.canceled.connect(lambda evt: print(f"CANCELED: {evt}"))
recognizer.session_stopped.connect(stop_cb)

recognizer.start_continuous_recognition()

try:
    import time
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopping continuous recognition...")
    recognizer.stop_continuous_recognition()
    print("Recognition stopped.")
