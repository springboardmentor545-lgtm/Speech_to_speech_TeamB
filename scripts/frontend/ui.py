import os
import tempfile
import streamlit as st
from scripts.backend.ultraaudio.config import (
    LANG_OPTIONS, TRANSLATE_OPTIONS, TTS_VOICE_MAP, LANG_CODE_NAME_MAP
)
from scripts.frontend.tabs.batch_studio import render_batch_studio
from scripts.frontend.tabs.live_stream import render_live_stream
from scripts.frontend.tabs.record_dub import render_record_dub
from scripts.frontend.tabs.history import render_history
from scripts.frontend.tabs.analytics import render_analytics
from scripts.frontend.tabs.remote_meeting import render_remote_meeting

def run_app():
    st.set_page_config(
        page_title="Ultra Audio Studio",
        page_icon="▶",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Session state initialization
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'temp_dir' not in st.session_state:
        st.session_state['temp_dir'] = tempfile.mkdtemp()
    if 'live_logs' not in st.session_state:
        st.session_state['live_logs'] = []
    
    import uuid
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())

    # Enhanced Premium Styling
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0a0e27 0%, #1a1d3a 50%, #2a1d4a 100%);
            color: #E8EAED;
            font-family: 'Poppins', sans-serif;
        }
        
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 30%, rgba(91, 86, 233, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(123, 106, 255, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: rgba(30, 33, 57, 0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #5B56E9 0%, #7B6AFF 100%); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, #7B6AFF 0%, #9B86FF 100%); }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            text-shadow: 0 0 20px rgba(91, 86, 233, 0.3);
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(19, 22, 43, 0.95) 0%, rgba(26, 29, 58, 0.95) 100%);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(91, 86, 233, 0.2);
        }
        
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(91, 86, 233, 0.15) 0%, rgba(30, 33, 57, 0.9) 100%);
            padding: 1.8rem;
            border-radius: 20px;
            border: 1px solid rgba(91, 86, 233, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        div[data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(91, 86, 233, 0.2), transparent);
            transition: left 0.5s;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 16px 48px rgba(91, 86, 233, 0.3), 0 0 40px rgba(91, 86, 233, 0.2);
        }
        
        div[data-testid="stMetric"]:hover::before { left: 100%; }
        
        .stButton > button {
            background: linear-gradient(135deg, #5B56E9 0%, #7B6AFF 50%, #9B86FF 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 16px;
            padding: 0.9rem 2.5rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 20px rgba(91, 86, 233, 0.5), 0 8px 32px rgba(91, 86, 233, 0.3);
            transition: all 0.3s;
            overflow: hidden;
            position: relative;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 32px rgba(91, 86, 233, 0.6), 0 12px 48px rgba(123, 106, 255, 0.4);
        }
        
        .stButton > button:hover::before { width: 300px; height: 300px; }
        
        .stSelectbox > div > div, .stTextInput > div > div > input {
            background: rgba(30, 33, 57, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(91, 86, 233, 0.3) !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            transition: all 0.3s;
        }
        
        .stSelectbox > div > div:hover {
            border-color: rgba(91, 86, 233, 0.5) !important;
            box-shadow: 0 0 20px rgba(91, 86, 233, 0.2);
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background: rgba(30, 33, 57, 0.4);
            backdrop-filter: blur(10px);
            padding: 8px;
            border-radius: 16px;
            border: 1px solid rgba(91, 86, 233, 0.2);
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 54px;
            background: transparent;
            border-radius: 12px;
            padding: 12px 24px;
            color: #A0A4B3;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(91, 86, 233, 0.1);
            color: #B8B4FF;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #5B56E9 0%, #7B6AFF 50%, #9B86FF 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 
                0 4px 20px rgba(91, 86, 233, 0.5), 
                0 8px 32px rgba(91, 86, 233, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }

        .chat-bubble {
            background: linear-gradient(135deg, rgba(30, 33, 57, 0.9) 0%, rgba(20, 23, 45, 0.8) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(91, 86, 233, 0.3);
            padding: 1.2rem;
            position: relative;
            animation: slideIn 0.5s ease-out;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .chat-bubble::before {
            content: '';
            position: absolute;
            left: -6px;
            top: 24px;
            width: 12px;
            height: 12px;
            background: linear-gradient(135deg, #5B56E9 0%, #7B6AFF 100%);
            border-radius: 50%;
            box-shadow: 0 0 16px rgba(91, 86, 233, 0.6);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 16px rgba(91, 86, 233, 0.6); }
            50% { box-shadow: 0 0 24px rgba(91, 86, 233, 0.9); }
        }
        
        .live-wave-bar {
            width: 8px;
            background: linear-gradient(180deg, #5B56E9 0%, #7B6AFF 100%);
            border-radius: 4px;
            transition: all 0.2s;
            margin: 0 3px;
            box-shadow: 0 0 10px rgba(91, 86, 233, 0.5);
        }
        
        .stVideo, .stAudio {
            border-radius: 20px;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6), 0 0 40px rgba(91, 86, 233, 0.2);
            border: 1px solid rgba(91, 86, 233, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced Header
    st.markdown("""
        <div style="padding: 2.5rem 0 2rem 0; text-align: center;">
            <div style="font-size: 4rem; background: linear-gradient(135deg, #5B56E9 0%, #8B86FF 50%, #BB96FF 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">
                ULTRA AUDIO STUDIO
            </div>
            <div style="color: #B8B4FF; font-size: 1.2rem; margin-top: 0.8rem; font-weight: 500;">
                ▶ AI-Powered Speech to Speech Translation Platform
            </div>
            <div style="margin-top: 1.5rem; padding: 0.8rem 2rem; background: linear-gradient(135deg, rgba(91, 86, 233, 0.15) 0%, rgba(91, 86, 233, 0.05) 100%);
                border-radius: 30px; display: inline-block; border: 1px solid rgba(91, 86, 233, 0.3); box-shadow: 0 4px 20px rgba(91, 86, 233, 0.2);">
                <span style="color: #6BE890; font-weight: 600;">● LIVE</span>
                <span style="color: #A0A4B3;"> | </span>
                <span style="color: #E8EAED; font-weight: 500;">Powered by Azure</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(91, 86, 233, 0.3), transparent);'>", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(91, 86, 233, 0.3);">
                <div style="font-size: 1.6rem; background: linear-gradient(135deg, #5B56E9 0%, #8B86FF 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">
                    ⚙ ENGINE CONTROLS
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("🌐 Language Settings", expanded=True):
            source_lang_name = st.selectbox("Source Language", list(LANG_OPTIONS.keys()), 0)
            target_lang_name = st.selectbox("Target Language", list(TRANSLATE_OPTIONS.keys()), 1)
            source_lang_code = LANG_OPTIONS[source_lang_name]
            target_lang_code = TRANSLATE_OPTIONS[target_lang_name]

        with st.expander("💼 Use Case"):
            use_case_profile = st.selectbox("Scenario", 
                ["General Conversation", "Healthcare", "Education", "Business", "Content Production",
                 "Legal", "Gaming", "Travel & Tourism", "News & Broadcast", "Customer Support", "Entertainment"], 0)
            CHUNK_DURATION_SEC = st.slider("Chunk Duration (sec)", 30, 120, 60, 15)

        with st.expander("🚀 Quality Mode", expanded=True):
            mode = st.radio("Mode", ["A - Full Ultra", "B - Balanced", "C - Basic"], index=1)
            if "A -" in mode:
                st.caption("✨ **Scene + Emotion + SpeakerID + LipSync** (heavy, highest fidelity)")
            elif "B -" in mode:
                st.caption("⚖️ **Scene + Emotion + LipSync** (balanced, recommended)")
            elif "C -" in mode:
                st.caption("⚡ **LipSync only / basic dub** (fast, minimal processing)")

        with st.expander("🎭 Voice Customization"):
            voice_style = st.selectbox("Voice Style", ["Neutral", "Expressive", "Identity-like"], 0)
            rate_val = st.slider("Speed", 0.8, 1.5, 1.0, 0.05)
            base_voice_rate = f"{int((rate_val - 1.0) * 100)}%" if rate_val != 1.0 else "0%"
            base_voice_pitch = st.select_slider("Pitch", ["x-low", "low", "medium", "high", "x-high"], value="medium")

        with st.expander("📡 Multi-Language Bridge"):
            bridge_enabled = st.checkbox("Enable Bridge Mode")
            bridge_target_names = []
            if bridge_enabled:
                bridge_target_names = st.multiselect("Additional Languages",
                    [n for n in TRANSLATE_OPTIONS.keys() if n != target_lang_name])
            bridge_target_codes = [TRANSLATE_OPTIONS[n] for n in bridge_target_names]
            bridge_lang_codes = list(dict.fromkeys([target_lang_code] + bridge_target_codes))

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📹 Batch Studio", "🎙 Live Stream", "🎤 Record & Dub", "📚 History", "📊 Analytics", "🤝 Remote Meeting"
    ])

    with tab1:
        render_batch_studio(
            temp_dir=st.session_state['temp_dir'],
            target_lang_name=target_lang_name,
            source_lang_name=source_lang_name,
            mode=mode,
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code,
            tts_voice_map=TTS_VOICE_MAP,
            chunk_duration_sec=CHUNK_DURATION_SEC,
            base_voice_rate=base_voice_rate,
            base_voice_pitch=base_voice_pitch
        )

    with tab2:
        render_live_stream(
            source_lang_name=source_lang_name,
            target_lang_name=target_lang_name,
            temp_dir=st.session_state['temp_dir'],
            use_case_profile=use_case_profile,
            bridge_enabled=bridge_enabled,
            bridge_target_names=bridge_target_names,
            bridge_lang_codes=bridge_lang_codes,
            base_voice_rate=base_voice_rate,
            base_voice_pitch=base_voice_pitch,
            voice_style=voice_style,
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code,
            tts_voice_map=TTS_VOICE_MAP
        )

    with tab3:
        render_record_dub(
            temp_dir=st.session_state['temp_dir'],
            target_lang_name=target_lang_name,
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code,
            tts_voice_map=TTS_VOICE_MAP,
            chunk_duration_sec=CHUNK_DURATION_SEC,
            base_voice_rate=base_voice_rate,
            base_voice_pitch=base_voice_pitch
        )

    with tab4:
        render_history(
            target_lang_name=target_lang_name,
            source_lang_name=source_lang_name,
            mode=mode
        )

    with tab5:
        render_analytics()

    with tab6:
        render_remote_meeting(
            source_lang_name=source_lang_name,
            target_lang_name=target_lang_name,
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code
        )