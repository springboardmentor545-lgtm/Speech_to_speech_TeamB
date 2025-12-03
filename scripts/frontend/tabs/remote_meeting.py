import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase, VideoProcessorBase
import av
import threading
import queue
import time
import base64
import os
import numpy as np
import azure.cognitiveservices.speech as speechsdk
from scripts.backend.ultraaudio.config import get_azure_configs, TTS_VOICE_MAP_FEMALE, TTS_VOICE_MAP_MALE
from scripts.backend.db import DatabaseManager

# --- Audio Processor ---
class AzureAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.lock = threading.Lock()
        self.is_muted = False

    def set_mute(self, muted):
        with self.lock:
            self.is_muted = muted

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # If muted, we still return the frame to keep the stream alive, but we don't process it
        # Actually, to "mute" effectively for the other side (if peer-to-peer), we should zero it out.
        # But here we are just sending to Azure.
        
        with self.lock:
            if self.is_muted:
                return frame # Don't send to Azure queue
        
        # Convert to 16kHz mono for Azure
        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
        resampled_frames = resampler.resample(frame)
        
        for r_frame in resampled_frames:
            audio_bytes = r_frame.to_ndarray().tobytes()
            self.audio_queue.put(audio_bytes)
            
        return frame

# --- Video Processor ---
class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.video_off = False
        self.lock = threading.Lock()

    def set_video_off(self, off):
        with self.lock:
            self.video_off = off

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        with self.lock:
            if self.video_off:
                # Return black frame
                img = frame.to_ndarray(format="bgr24")
                black_img = np.zeros(img.shape, dtype=np.uint8)
                return av.VideoFrame.from_ndarray(black_img, format="bgr24")
        return frame

# --- Helper: Synthesize Speech ---
def synthesize_speech(text, target_lang, voice_name):
    """Synthesize text to speech using Azure and return base64 audio."""
    try:
        speech_key, service_region = get_azure_configs()
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Use null output to prevent server-side playback, we just want the bytes
        null_audio_config = speechsdk.audio.AudioConfig(filename=os.devnull)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=null_audio_config)
        
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return base64.b64encode(result.audio_data).decode('utf-8')
        else:
            print(f"TTS Error: {result.reason}")
            return None
    except Exception as e:
        print(f"TTS Exception: {e}")
        return None

# --- Azure Thread ---
def start_azure_recognition(processor, source_lang, target_lang, result_queue, stop_event, room_id, username, target_voice):
    speech_key, service_region = get_azure_configs()
    
    # Translation Config
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=speech_key, 
        region=service_region,
        speech_recognition_language=source_lang,
        target_languages=[target_lang]
    )
    
    # Push Stream
    push_stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    
    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config, 
        audio_config=audio_config
    )
    
    db = DatabaseManager()

    def result_callback(evt):
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            original = evt.result.text
            translated = evt.result.translations[target_lang]
            
            if original.strip():
                # 1. Synthesize the translated text to audio
                audio_b64 = synthesize_speech(translated, target_lang, target_voice)
                
                # 2. Save to DB with audio
                db.add_message(room_id, username, original, translated, target_lang, audio_b64)
                
                # 3. Put in queue for local UI update
                result_queue.put({
                    "user": username,
                    "original": original,
                    "translated": translated,
                    "audio": audio_b64
                })

    recognizer.recognized.connect(result_callback)
    recognizer.start_continuous_recognition()

    try:
        while not stop_event.is_set():
            try:
                chunk = processor.audio_queue.get(timeout=0.5)
                push_stream.write(chunk)
            except queue.Empty:
                continue
            
            # Heartbeat update
            db.update_heartbeat(room_id, username)
            
    finally:
        recognizer.stop_continuous_recognition()
        push_stream.close()


def render_remote_meeting(
    source_lang_name,
    target_lang_name,
    source_lang_code,
    target_lang_code
):
    st.markdown("## 🌍 Remote Meeting with Live Dubbing")
    
    # Initialize Session State
    if 'meeting_joined' not in st.session_state:
        st.session_state.meeting_joined = False
    if 'room_id' not in st.session_state:
        st.session_state.room_id = ""
    if 'username' not in st.session_state:
        st.session_state.username = ""

    # --- LOBBY VIEW ---
    if not st.session_state.meeting_joined:
        st.caption("Join a room to start communicating. Your speech will be translated and broadcasted.")
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                u_name = st.text_input("Your Name", placeholder="Enter your name", key="lobby_name")
            with c2:
                r_id = st.text_input("Room ID", placeholder="e.g. Room101", key="lobby_room")
            
            if st.button("Join / Create Room", type="primary", use_container_width=True):
                if u_name and r_id:
                    st.session_state.username = u_name
                    st.session_state.room_id = r_id
                    st.session_state.meeting_joined = True
                    st.rerun()
                else:
                    st.warning("Please enter both Name and Room ID.")
        return

    # --- MEETING VIEW ---
    
    # Sidebar Controls
    with st.sidebar:
        st.markdown(f"### 🏠 Room: {st.session_state.room_id}")
        st.markdown(f"👤 **{st.session_state.username}**")
        
        if st.button("Leave Room", type="secondary"):
            st.session_state.meeting_joined = False
            st.rerun()
            
        st.divider()
        st.markdown("### 👥 Participants")
        db = DatabaseManager()
        participants = db.get_participants(st.session_state.room_id)
        if participants:
            for p in participants:
                st.markdown(f"- {p} {'(You)' if p == st.session_state.username else ''}")
        else:
            st.markdown("- *Waiting...*")
            
        st.divider()
        
        # Voice Selection for Dubbing
        st.markdown("### 🗣️ Dubbing Voice")
        gender = st.radio("Voice Gender", ["Female", "Male"], horizontal=True)
        voice_map = TTS_VOICE_MAP_MALE if gender == "Male" else TTS_VOICE_MAP_FEMALE
        target_voice = voice_map.get(target_lang_code, "en-US-JennyNeural") 
        st.info(f"Target Voice: {target_voice}")

    # Main Interface
    col_video, col_chat = st.columns([1.5, 1])

    with col_video:
        st.markdown("#### 📹 Live Stream")
        
        # Controls
        c_mute, c_video = st.columns(2)
        is_muted = c_mute.checkbox("🔇 Mute Mic", value=False)
        is_video_off = c_video.checkbox("📷 Turn Off Camera", value=False)
        
        # WebRTC Context
        ctx = webrtc_streamer(
            key="remote-meeting-shared",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AzureAudioProcessor,
            video_processor_factory=VideoProcessor,
            media_stream_constraints={"video": True, "audio": True},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            video_html_attrs={"style": {"width": "100%", "border-radius": "12px", "overflow": "hidden"}},
        )
        
        # Apply Controls to Processors
        if ctx.audio_processor:
            ctx.audio_processor.set_mute(is_muted)
        if ctx.video_processor:
            ctx.video_processor.set_video_off(is_video_off)

    # Initialize State
    if 'meeting_queue' not in st.session_state:
        st.session_state.meeting_queue = queue.Queue()
    if 'stop_event' not in st.session_state:
        st.session_state.stop_event = threading.Event()
    if 'azure_thread' not in st.session_state:
        st.session_state.azure_thread = None

    # Handle Processing Start/Stop
    if ctx.state.playing and not st.session_state.azure_thread:
        st.session_state.stop_event.clear()
        if ctx.audio_processor:
            t = threading.Thread(
                target=start_azure_recognition,
                args=(
                    ctx.audio_processor, 
                    source_lang_code, 
                    target_lang_code, 
                    st.session_state.meeting_queue, 
                    st.session_state.stop_event,
                    st.session_state.room_id,
                    st.session_state.username,
                    target_voice
                ),
                daemon=True
            )
            t.start()
            st.session_state.azure_thread = t
            st.toast("Connected to Meeting", icon="🟢")

    elif not ctx.state.playing and st.session_state.azure_thread:
        st.session_state.stop_event.set()
        st.session_state.azure_thread.join()
        st.session_state.azure_thread = None
        st.toast("Disconnected", icon="🔴")

    # --- Chat & Dubbing Interface ---
    with col_chat:
        st.markdown("#### 💬 Live Transcript & Audio")
        
        chat_container = st.container(height=500, border=True)
        
        # Poll Database
        messages = db.get_messages(st.session_state.room_id, limit=20) 
        
        with chat_container:
            if not messages:
                st.info("No messages yet. Start speaking!")
            
            for msg in messages:
                # msg: (user, original, translated, timestamp, lang_code, audio_base64)
                m_user, m_orig, m_trans, m_time, m_lang, m_audio = msg
                
                is_me = (m_user == st.session_state.username)
                align = "flex-end" if is_me else "flex-start"
                bg_color = "rgba(91, 86, 233, 0.2)" if is_me else "rgba(255, 255, 255, 0.05)"
                border_color = "#5B56E9" if is_me else "#444"
                
                with st.container():
                    st.markdown(f"""
                    <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                        <div style="
                            background: {bg_color}; 
                            border: 1px solid {border_color}; 
                            border-radius: 12px; 
                            padding: 10px; 
                            max-width: 85%;
                        ">
                            <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 4px;">
                                <strong>{m_user}</strong> • {m_time}
                            </div>
                            <div style="color: #ddd; font-style: italic; font-size: 0.9rem;">"{m_orig}"</div>
                            <div style="color: #6BE890; font-weight: 600; margin-top: 4px;">{m_trans}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Audio Player for Dubbing
                    if m_audio:
                        if not is_me:
                            st.markdown(f"""
                                <audio controls autoplay style="width: 100%; height: 30px; margin-top: 5px;">
                                    <source src="data:audio/wav;base64,{m_audio}" type="audio/wav">
                                </audio>
                            """, unsafe_allow_html=True)
                        else:
                             st.markdown(f"""
                                <audio controls style="width: 100%; height: 30px; margin-top: 5px;">
                                    <source src="data:audio/wav;base64,{m_audio}" type="audio/wav">
                                </audio>
                            """, unsafe_allow_html=True)


    # Auto-refresh for real-time feel
    if ctx.state.playing:
        time.sleep(1.5) 
        st.rerun()

