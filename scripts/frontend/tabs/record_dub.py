import os
import streamlit as st
from scripts.backend.ultraaudio.pipeline import run_pipeline

def render_record_dub(
    temp_dir,
    target_lang_name,
    source_lang_code,
    target_lang_code,
    tts_voice_map,
    chunk_duration_sec,
    base_voice_rate,
    base_voice_pitch
):
    st.markdown("## 🎙️ Instant Voice Dubbing")
    st.caption("Record a short message, and the system will instantly translate and dub it into the target language.")

    col_rec, col_result = st.columns([1, 1])
    rec_path = None
    
    with col_rec:
        st.markdown("#### Record Your Message")
        
        rec_method = st.radio("Input Method", ["Microphone", "File Upload"], horizontal=True, key="tab3_rec_method")
        
        if rec_method == "Microphone":
            try:
                audio_val = st.audio_input("Record Voice", key="tab3_mic")
                if audio_val:
                    rec_path = os.path.join(temp_dir, "mic_recording.wav")
                    with open(rec_path, "wb") as f:
                        f.write(audio_val.getbuffer())
                    st.success("Recording captured successfully.")
            except AttributeError:
                st.error("`st.audio_input` is not available in this version of Streamlit. Please upgrade or use File Upload.")
            except Exception as e:
                st.error(f"Error recording audio: {e}")

        else:
            upload_record = st.file_uploader("Upload recorded WAV or MP3", type=['wav', 'mp3'], key='rec_upload')
            if upload_record:
                rec_path = os.path.join(temp_dir, "file_upload_recording.wav")
                try:
                    with open(rec_path, "wb") as f:
                        f.write(upload_record.getbuffer())
                    st.success("Audio file loaded.")
                except Exception as e:
                    st.error(f"Could not process file: {e}")

        if rec_path:
            st.markdown("#### Original Audio Playback")
            st.audio(rec_path)
            if st.button(f"Translate & Dub Recording to {target_lang_name}", type="primary", width='stretch'):
                with st.spinner("Processing short audio segment..."):
                    is_vid = False
                    run_pipeline(rec_path, is_vid, source_lang_code, target_lang_code, tts_voice_map.get(target_lang_code), chunk_duration_sec, base_voice_rate, base_voice_pitch, "Recorded Audio", target_lang_name, "Instant Dub")
                st.toast("Instant dubbing complete!")

    with col_result:
        st.markdown("#### Translated Output")
        if st.session_state['history'] and st.session_state['history'][-1].get('audio_path'):
            latest = st.session_state['history'][-1]
            if not latest.get('video_path'): 
                st.audio(latest['audio_path'])
                st.download_button("Download Dubbed Audio 🎧", open(latest['audio_path'], "rb"), file_name="instant_dubbed_audio.wav", type="secondary", width='stretch')
        else:
            st.info("The translated audio will appear here.")
