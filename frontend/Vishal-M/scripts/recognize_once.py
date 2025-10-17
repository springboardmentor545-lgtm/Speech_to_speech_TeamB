import azure.cognitiveservices.speech as speechsdk

speech_key = "YOUR_SPEECH_KEY"
service_region = "YOUR_REGION"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Say something...")
result = recognizer.recognize_once_async().get()
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
else:
    print("No match or cancelled:", result.reason)
