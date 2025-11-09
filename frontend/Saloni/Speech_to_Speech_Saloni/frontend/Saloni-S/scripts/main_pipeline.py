# main_pipeline.py
import os, time
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from translate_text import translate_text
from text_to_speech import synthesize_speech

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

def recognize_once():
    cfg = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    rec = speechsdk.SpeechRecognizer(speech_config=cfg)
    print("🎤 Speak...")
    res = rec.recognize_once_async().get()
    if res.reason == speechsdk.ResultReason.RecognizedSpeech:
        return res.text
    return ""

def run(target_lang="hi", voice="hi-IN-SwaraNeural"):
    t0 = time.time()
    src = recognize_once()
    t1 = time.time()
    if not src.strip():
        print("No speech recognized"); return
    tgt = translate_text(src, target_lang)
    t2 = time.time()
    out = synthesize_speech(tgt, voice=voice, out_path=f"../samples/output/s2s_{target_lang}.wav")
    t3 = time.time()
    print("STT:", t1-t0, "Trans:", t2-t1, "TTS:", t3-t2, "Total:", t3-t0)
    print("Saved:", out)

if __name__ == "__main__":
    run()
