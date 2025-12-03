import os
import time
import base64
import queue
import streamlit as st
import av
import threading
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
from scripts.backend.ultraaudio.orchestrator import LiveTranslationOrchestrator
from scripts.backend.ultraaudio.config import LANG_CODE_NAME_MAP

class LiveAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.orchestrator = None
        self.resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
        self.lock = threading.Lock()

    def set_orchestrator(self, orchestrator):
        with self.lock:
            self.orchestrator = orchestrator

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        with self.lock:
            if self.orchestrator and self.orchestrator.is_running:
                try:
                    # Resample to 16kHz mono for Azure
                    resampled_frames = self.resampler.resample(frame)
                    for r_frame in resampled_frames:
                        audio_bytes = r_frame.to_ndarray().tobytes()
                        self.orchestrator.ingest_audio(audio_bytes)
                except Exception as e:
                    print(f"WebRTC Audio Error: {e}")
        return frame

def render_live_stream(
    source_lang_name,
    target_lang_name,
    temp_dir,
    use_case_profile,
    bridge_enabled,
    bridge_target_names,
    bridge_lang_codes,
    base_voice_rate,
    base_voice_pitch,
    voice_style,
    source_lang_code,
    target_lang_code,
    tts_voice_map
):
    st.markdown("## 📡 Real-Time Speech Translation Bridge")
    st.caption(f"Translate from **{source_lang_name}** to **{target_lang_name}** with real-time audio output.")
    
    col_ctrl, col_disp = st.columns([1, 2])

    with col_ctrl:
        st.markdown("#### Input & Reference")
        live_mode = st.radio("Input Source", ["Microphone", "File Simulation"], horizontal=True, key="live_mode")
        
        sim_file = None
        if live_mode == "File Simulation":
            sim_upl = st.file_uploader("Upload source WAV file (Simulation)", type=['wav'], key="sim_file_upload")
            if sim_upl:
                sim_file = os.path.join(temp_dir, "sim.wav")
                with open(sim_file, "wb") as f:
                    f.write(sim_upl.getbuffer())

        c_start, c_stop = st.columns(2)
        
        # Logic for Start/Stop
        if live_mode == "File Simulation":
            start_btn = c_start.button("Start Simulation ⚡", type="primary", width='stretch')
            stop_btn = c_stop.button("Stop Session 🛑", width='stretch')
        else:
            # For Microphone, we use WebRTC streamer which acts as the "Start" mechanism
            # But we still need to initialize the orchestrator
            if 'orchestrator' not in st.session_state or not st.session_state.orchestrator.is_running:
                start_btn = c_start.button("Initialize Engine ⚡", type="primary", width='stretch')
            else:
                start_btn = False
                c_start.success("Engine Ready")
            
            stop_btn = c_stop.button("Stop Engine 🛑", width='stretch')

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Session Profile")
        st.caption(f"**Use case:** *{use_case_profile}*")
        if bridge_enabled:
            st.caption(f"**Bridge Languages:** *{', '.join(bridge_target_names)}* (Text Only)")
        else:
            st.caption("**Mode:** Single-language Speech-to-Speech.")


    with col_disp:
        st.markdown("#### Live Metrics")
        m1, m2, m3, m4 = st.columns(4)
        p95_m = m1.empty(); p99_m = m2.empty(); bleu_m = m3.empty(); prec_m = m4.empty()
        p95_m.metric("Latency (P95)", "0 ms", delta="P95 Latency")
        p99_m.metric("Latency (P99)", "0 ms", delta="P99 Latency")
        bleu_m.metric("Quality (BLEU)", "0.0", delta="Translation Quality")
        prec_m.metric("Confidence Index", "0.0", delta="Model Confidence")

        visualizer_placeholder = st.empty()
        st.markdown("#### Real-Time Transcript & Logs")
        chat_placeholder = st.empty()
        st.markdown("#### Latency Heat Map (Last 20 Segments)")
        heat_placeholder = st.empty()

    # Initialize logs if not present
    if 'live_logs' not in st.session_state:
        st.session_state.live_logs = []

    # --- Start Logic ---
    if start_btn:
        if live_mode == "File Simulation" and not sim_file:
            st.error("Please upload a simulation file first.")
        else:
            # Stop existing if running
            if 'orchestrator' in st.session_state and st.session_state.orchestrator.is_running:
                st.session_state.orchestrator.stop_pipeline()
                time.sleep(0.5)

            # Clear logs on new start
            st.session_state.live_logs = []
            
            voice_map = tts_voice_map.copy()
            
            # Determine input type for Orchestrator
            orch_input_type = "WebRTC" if live_mode == "Microphone" else "File Simulation"
            
            st.session_state.orchestrator = LiveTranslationOrchestrator(
                source_lang=source_lang_code,
                primary_target_lang=target_lang_code,
                bridge_langs=bridge_lang_codes if bridge_enabled else [target_lang_code],
                voice_map=voice_map,
                voice_rate=base_voice_rate,
                voice_pitch=base_voice_pitch,
                voice_style=voice_style
            )
            st.session_state.orchestrator.start_pipeline(orch_input_type, sim_file)
            st.toast("Engine initialized.", icon="⚡")
            st.rerun()

    # --- Stop Logic ---
    if stop_btn and 'orchestrator' in st.session_state:
        st.session_state.orchestrator.stop_pipeline()
        st.toast("Engine stopped.", icon="🛑")

    # --- WebRTC Streamer (Only for Microphone Mode) ---
    if live_mode == "Microphone":
        with col_ctrl:
            st.markdown("#### 🎤 Microphone Input")
            if 'orchestrator' in st.session_state and st.session_state.orchestrator.is_running:
                ctx = webrtc_streamer(
                    key="live-stream-mic",
                    mode=WebRtcMode.SENDONLY,
                    audio_processor_factory=LiveAudioProcessor,
                    media_stream_constraints={"video": False, "audio": True},
                    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
                )
                
                # Connect Processor to Orchestrator
                if ctx.audio_processor:
                    ctx.audio_processor.set_orchestrator(st.session_state.orchestrator)
            else:
                st.info("Click 'Initialize Engine' to enable microphone.")

    # Download Transcript Button
    if 'live_logs' in st.session_state and st.session_state.live_logs:
        import pandas as pd
        df_logs = pd.DataFrame(st.session_state.live_logs)
        if not df_logs.empty:
            csv = df_logs.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "Download Transcript (CSV) 📥",
                csv,
                "live_transcript.csv",
                "text/csv",
                key='download-csv'
            )

    if 'orchestrator' in st.session_state:
        orch = st.session_state.orchestrator
        
        if orch.is_running:
            st.sidebar.markdown(f'<p style="font-weight: 600; color: #6BE890;"><span class="status-dot"></span>Live Status: RUNNING</p>', unsafe_allow_html=True)
            
            while orch.is_running:
                try:
                    while not orch.result_queue.empty():
                        item = orch.result_queue.get_nowait()
                        st.session_state.live_logs.append(item) 
                except queue.Empty:
                    pass

                # Visualizer HTML - Dynamic Reactive
                import random
                is_active = orch.is_voice_active()
                
                bars_html = ""
                if is_active:
                    label_html = '<div class="live-visualizer-label" style="margin-right: 15px; color: #6BE890;">🔴 Listening...</div>'
                    for _ in range(12): 
                        h = random.randint(20, 100)
                        dur = random.uniform(0.3, 0.8)
                        bars_html += f'<div class="live-wave-bar" style="height: {h}%; animation-duration: {dur}s; background: linear-gradient(180deg, #6BE890, #3A379C);"></div>'
                else:
                    label_html = '<div class="live-visualizer-label" style="margin-right: 15px; color: #A0A4B3;">⚪ Idle</div>'
                    for _ in range(12):
                        h = 5 
                        bars_html += f'<div class="live-wave-bar" style="height: {h}%; background: #3A3F50;"></div>'

                visualizer_html = f"""
                <div class="live-visualizer-container">
                    {label_html}
                    <div class="live-wave-bars" style="height: 40px; display: flex; align-items: flex-end; gap: 4px;">
                        {bars_html}
                    </div>
                </div>
                """
                visualizer_placeholder.markdown(visualizer_html, unsafe_allow_html=True)

                if st.session_state.live_logs:
                    recent_logs = st.session_state.live_logs[-8:]
                    chat_html = '<div class="chat-container">'
                    for log in recent_logs:
                        lang_code = log.get("lang", target_lang_code)
                        lang_name = LANG_CODE_NAME_MAP.get(lang_code, lang_code)
                        conf = log.get("confidence", 0.0)
                        
                        status_icon = "✨" if lang_code == target_lang_code else "💬"
                        
                        chat_html += f"""
<div class="chat-bubble">
    <div class="chat-meta">
        <span>{status_icon} {lang_name}</span>
        <span>Latency: {log.get('latency', 0):.0f} ms</span>
        <span>Conf: {conf:.0f}%</span>
        <span>{log.get('timestamp', '')}</span>
    </div>
    <div><strong>Original:</strong> {log.get('original', '')}</div>
    <div style="color: #6BE890; margin-top:4px;"><strong>Translated:</strong> {log.get('translated', '')}</div>
</div>
"""
                    chat_html += '</div>'
                    chat_placeholder.markdown(chat_html, unsafe_allow_html=True)

                    # Latency Heat Map
                    heat_logs = st.session_state.live_logs[-20:]
                    heat_html = '<div style="display:flex;gap:4px;margin-top:8px;">'
                    for log in heat_logs:
                        latency = log.get("latency", 0.0) or 0.0
                        if latency < 250:
                            color = "#6BE890" 
                        elif latency < 700:
                            color = "#FFC84A" 
                        else:
                            color = "#FF7070" 
                        
                        conf_height = max(5, int(log.get("confidence", 0.0) * 0.2)) 
                        
                        heat_html += f'<div title="{LANG_CODE_NAME_MAP.get(log.get("lang", "-"))}: {latency:.0f} ms | Conf: {log.get("confidence", 0.0):.0f}%" style="width:10px;height:{conf_height}px;border-radius:2px;background:{color}; transition: height 0.3s ease;"></div>'
                    heat_html += '</div>'
                    heat_placeholder.markdown(heat_html, unsafe_allow_html=True)
                else:
                    chat_placeholder.info("Awaiting live audio input...")
                    heat_placeholder.empty()

                p95, p99, bleu, pgram = orch.get_stats()
                p95_m.metric("Latency (P95)", f"{p95:.0f} ms", delta="P95 Latency")
                p99_m.metric("Latency (P99)", f"{p99:.0f} ms", delta="P99 Latency")
                bleu_m.metric("Quality Est.", f"{bleu:.1f}", delta="Translation Quality")
                prec_m.metric("Confidence Index", f"{pgram:.1f}%", delta="Model Confidence")

                # Audio Playback
                try:
                    while not orch.audio_queue.empty():
                        audio_bytes = orch.audio_queue.get_nowait()
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        audio_html = f'<audio src="data:audio/wav;base64,{audio_base64}" autoplay="autoplay" style="display:none;"></audio>'
                        st.markdown(audio_html, unsafe_allow_html=True)
                except queue.Empty:
                    pass

                time.sleep(0.03)
        
        # --- Post-Loop / Stopped State Rendering ---
        try:
            while not orch.result_queue.empty():
                item = orch.result_queue.get_nowait()
                st.session_state.live_logs.append(item)
        except:
            pass
        
        if st.session_state.live_logs:
            recent_logs = st.session_state.live_logs[-8:]
            chat_html = '<div class="chat-container">'
            for log in recent_logs:
                if log.get("lang") == "Error":
                    st.error(f"❌ {log['original']}") 
                    chat_html += f"""
                    <div class="chat-bubble" style="border-left: 4px solid #FF4B4B; background: rgba(255, 75, 75, 0.1);">
                        <div class="chat-meta" style="color: #FF4B4B;">❌ SYSTEM ERROR - {log['timestamp']}</div>
                        <div style="color: #FF4B4B;"><strong>{log['original']}</strong></div>
                    </div>
                    """
                else:
                    lang_code = log.get("lang", target_lang_code)
                    lang_name = LANG_CODE_NAME_MAP.get(lang_code, lang_code)
                    conf = log.get("confidence", 0.0)
                    status_icon = "✨" if lang_code == target_lang_code else "💬"
                    chat_html += f"""
<div class="chat-bubble">
    <div class="chat-meta">
        <span>{status_icon} {lang_name}</span>
        <span>Latency: {log.get('latency', 0):.0f} ms</span>
        <span>Conf: {conf:.0f}%</span>
        <span>{log.get('timestamp', '')}</span>
    </div>
    <div><strong>Original:</strong> {log.get('original', '')}</div>
    <div style="color: #6BE890; margin-top:4px;"><strong>Translated:</strong> {log.get('translated', '')}</div>
</div>
"""
            chat_html += '</div>'
            chat_placeholder.markdown(chat_html, unsafe_allow_html=True)
        
        if not orch.is_running:
            st.sidebar.markdown(f'<p style="font-weight: 600; color: #FF4B4B;"><span class="status-dot" style="background: #FF4B4B;"></span>Live Status: STOPPED</p>', unsafe_allow_html=True)
