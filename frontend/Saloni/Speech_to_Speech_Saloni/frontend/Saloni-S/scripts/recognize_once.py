# recognize_once.py
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Speak now...")
res = recognizer.recognize_once_async().get()
print("TEXT:", getattr(res, "text", ""))
