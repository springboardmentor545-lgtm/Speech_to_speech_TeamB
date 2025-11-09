import os, time, sys
import streamlit as st
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# Ensure local scripts import
sys.path.append(os.path.abspath("./frontend/Saloni-S/scripts"))
from translate_text import translate_text
from text_to_speech import synthesize_speech

# Load environment variables
load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION")

# Streamlit page setup
st.set_page_config(page_title="Speech-to-Speech Translator", page_icon="🎤", layout="centered")
st.title("🎤 Speech-to-Speech Translator")
st.caption("Azure STT → Azure Translator → Azure TTS")

# Target language options
LANGUAGE_MAP = {
    "Hindi": ("hi", "hi-IN-SwaraNeural"),
    "French": ("fr", "fr-FR-DeniseNeural"),
    "Spanish": ("es", "es-ES-ElviraNeural"),
    "German": ("de", "de-DE-KatjaNeural"),
    "Tamil": ("ta", "ta-IN-PallaviNeural"),
    "Telugu": ("te", "te-IN-ShrutiNeural"),
    "Marathi": ("mr", "mr-IN-AarohiNeural"),
    "Bengali": ("bn", "bn-IN-TanishaaNeural"),
    "Gujarati": ("gu", "gu-IN-NiranjanNeural"),
    "Punjabi": ("pa", "pa-IN-AmritNeural"),
    "Kannada": ("kn", "kn-IN-SapnaNeural"),
    "Malayalam": ("ml", "ml-IN-SobhanaNeural"),
}

# Sidebar info
with st.sidebar:
    st.header("Settings")
    target_name = st.selectbox("Target Language", list(LANGUAGE_MAP.keys()), index=0)
    st.markdown("---")
    st.write("🎙️ Step 1: Click **Recognize** and speak clearly")
    st.write("🌍 Step 2: Wait for translation")
    st.write("🔊 Step 3: Hear your translated voice")

col1, col2 = st.columns(2)
with col1:
    recognize = st.button("🎙️ Recognize")
with col2:
    st.info("Use your system microphone")

# When user clicks the Recognize button
if recognize:
    if not SPEECH_KEY or not SERVICE_REGION:
        st.error("Missing SPEECH_KEY / SERVICE_REGION in .env file ❌")
    else:
        try:
            # Add explicit audio config (fix for mic not detected)
            st.spinner("Listening...")
            t0 = time.time()
            speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  # 👈 fix line
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            
            st.write("🎧 Listening... Please speak now!")
            res = recognizer.recognize_once_async().get()
            st.write("---")

            # Check result
            if res.reason == speechsdk.ResultReason.RecognizedSpeech:
                st.subheader("📝 Recognized Text")
                st.write(res.text)

                tgt_code, voice = LANGUAGE_MAP[target_name]
                t1 = time.time()
                translated = translate_text(res.text, tgt_code)
                t2 = time.time()

                st.subheader(f"🌍 Translated Text → {target_name}")
                st.write(translated)

                out_path = f"frontend/Saloni-S/samples/output/gui_{tgt_code}.wav"
                synthesize_speech(translated, voice=voice, out_path=out_path)
                t3 = time.time()

                st.subheader("🔊 Audio Output")
                with open(out_path, "rb") as f:
                    st.audio(f.read(), format="audio/wav")

                st.success(f"✅ Done in {t3 - t0:.2f}s (STT {t1 - t0:.2f}s • Trans {t2 - t1:.2f}s • TTS {t3 - t2:.2f}s)")
            else:
                st.warning("⚠️ No speech recognized — try speaking a bit louder or closer to mic.")
                if res.reason == speechsdk.ResultReason.Canceled:
                    details = res.cancellation_details
                    st.error(f"Recognition canceled: {details.reason}")
                    if details.error_details:
                        st.error(f"Error details: {details.error_details}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
