# text_to_speech.py
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

if not SPEECH_KEY or not SERVICE_REGION:
    raise EnvironmentError("SPEECH_KEY or SERVICE_REGION missing in .env")

def synthesize_speech(text: str, voice: str = "en-US-JennyNeural", out_path: str = "output.wav") -> str:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    speech_config.speech_synthesis_voice_name = voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return out_path
    else:
        raise RuntimeError(f"TTS failed: {result.reason}")
