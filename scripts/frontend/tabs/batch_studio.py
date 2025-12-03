import os
import streamlit as st
import yt_dlp
import uuid
from scripts.backend.ultraaudio.pipeline import run_pipeline
from scripts.backend.ultraaudio.config import TTS_VOICE_MAP_MALE, TTS_VOICE_MAP_FEMALE

def render_batch_studio(
    temp_dir,
    target_lang_name,
    source_lang_name,
    mode,
    source_lang_code,
    target_lang_code,
    tts_voice_map,
    chunk_duration_sec,
    base_voice_rate,
    base_voice_pitch
):
    st.markdown("## 🎬 Media Auto-Dubbing Workflow")
    st.caption("Upload a video/audio file or paste a YouTube link. The original audio track will be replaced with the translated voice track.")

    # Initialize session state for video path if not exists
    if 'downloaded_video_path' not in st.session_state:
        st.session_state['downloaded_video_path'] = None

    # Sync History from DB
    from scripts.backend.db import DatabaseManager
    try:
        db = DatabaseManager()
        # DB returns newest first. Session state expects oldest first (append order).
        session_id = st.session_state.get('session_id')
        db_history = db.get_history(session_id)
        st.session_state['history'] = db_history[::-1]
    except Exception as e:
        print(f"Failed to sync history: {e}")
        if 'history' not in st.session_state:
            st.session_state['history'] = []

    col_in, col_prev = st.columns([1, 1])

    with col_in:
        input_method = st.radio("Source Input Type", ("YouTube URL", "Upload File"), horizontal=True, key="batch_input_method")
        
        # Use session state path if available
        video_path = st.session_state.get('downloaded_video_path')
        audio_only_path = None

        with st.container(border=True):
            if input_method == "YouTube URL":
                search_query = st.text_input("Search YouTube or Paste URL", placeholder="Enter keywords or paste link...", key="youtube_url")
                
                if 'search_results' not in st.session_state:
                    st.session_state['search_results'] = []
                
                if search_query:
                    # Check if it's a URL or a search query
                    is_url = "youtube.com" in search_query or "youtu.be" in search_query
                    
                    if is_url:
                        # Direct URL handling
                        if st.button("Fetch Video"):
                            with st.spinner("Fetching video information..."):
                                try:
                                    # Generate unique filename
                                    unique_id = str(uuid.uuid4())[:8]
                                    
                                    # Clean up previous file
                                    prev_path = st.session_state.get('downloaded_video_path')
                                    if prev_path and os.path.exists(prev_path):
                                        try:
                                            os.remove(prev_path)
                                        except:
                                            pass

                                    ydl_opts = {
                                        'outtmpl': os.path.join(temp_dir, f'downloaded_video_{unique_id}.%(ext)s'),
                                        'format': 'best[ext=mp4]/best', # Prioritize single file to reduce merge errors
                                        'noplaylist': True,
                                        'quiet': False, # Enable output for debugging logs
                                        'nocheckcertificate': True,
                                        'no_warnings': False,
                                        'force_ipv4': True,
                                        'socket_timeout': 30,
                                        'source_address': '0.0.0.0', # Bind to IPv4
                                        'http_headers': {
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                            'Accept-Language': 'en-us,en;q=0.5',
                                        }
                                    }
                                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                        ydl.download([search_query])
                                    # Find the downloaded file
                                    found_path = None
                                    for ext in ['.mp4', '.mkv', '.webm']:
                                        possible_path = os.path.join(temp_dir, f'downloaded_video_{unique_id}{ext}')
                                        if os.path.exists(possible_path):
                                            found_path = possible_path
                                            break
                                    
                                    if found_path:
                                        # Check if file is empty
                                        if os.path.getsize(found_path) > 0:
                                            st.session_state['downloaded_video_path'] = found_path
                                            st.success(f"Video downloaded successfully!")
                                            st.rerun()
                                        else:
                                            st.error("The downloaded file is empty. YouTube might be blocking the server IP.")
                                            st.warning("👉 Please try using the 'Upload File' option instead.")
                                            try:
                                                os.remove(found_path)
                                            except:
                                                pass
                                    else:
                                        st.error("Download failed or file not found.")
                                        st.warning("👉 Please try using the 'Upload File' option instead.")
                                except Exception as e:
                                    st.error(f"Error while downloading: {e}")
                    else:
                        # Search functionality
                        if st.button("🔍 Search YouTube"):
                            with st.spinner(f"Searching for '{search_query}'..."):
                                try:
                                    ydl_opts = {
                                        'quiet': True,
                                        'default_search': 'ytsearch5',
                                        'noplaylist': True,
                                        'ignoreerrors': True,
                                        'no_warnings': True,
                                        'extract_flat': False 
                                    }
                                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                        info = ydl.extract_info(search_query, download=False)
                                        if info:
                                            if 'entries' in info:
                                                valid_entries = [e for e in info['entries'] if e is not None]
                                                st.session_state['search_results'] = valid_entries
                                            else:
                                                st.session_state['search_results'] = [info]
                                        
                                        if not st.session_state['search_results']:
                                            st.warning("No results found. Try a different keyword.")
                                except Exception as e:
                                    st.error(f"Search failed: {e}")

                        # Display search results
                        if st.session_state['search_results']:
                            st.markdown("### Search Results")
                            for idx, entry in enumerate(st.session_state['search_results']):
                                with st.container():
                                    c1, c2 = st.columns([1, 3])
                                    with c1:
                                        thumb = entry.get('thumbnail')
                                        if thumb:
                                            st.image(thumb, width='stretch')
                                        else:
                                            st.markdown("📷 *No Image*")
                                    with c2:
                                        st.markdown(f"**{entry.get('title', 'Unknown Title')}**")
                                        
                                        # Format duration
                                        dur_sec = entry.get('duration')
                                        dur_str = "N/A"
                                        if dur_sec:
                                            try:
                                                import datetime
                                                dur_str = str(datetime.timedelta(seconds=int(dur_sec)))
                                            except:
                                                pass
                                        
                                        st.caption(f"Channel: {entry.get('uploader', 'Unknown')} | Duration: {dur_str}")
                                        if st.button(f"Select Video", key=f"sel_vid_{idx}"):
                                            vid_url = entry.get('url') or entry.get('webpage_url')
                                            if vid_url:
                                                with st.spinner("Downloading selected video..."):
                                                    try:
                                                        # Generate unique filename
                                                        unique_id = str(uuid.uuid4())[:8]
                                                        
                                                        # Clean up previous file
                                                        prev_path = st.session_state.get('downloaded_video_path')
                                                        if prev_path and os.path.exists(prev_path):
                                                            try:
                                                                os.remove(prev_path)
                                                            except:
                                                                pass

                                                        ydl_opts = {
                                                            'outtmpl': os.path.join(temp_dir, f'downloaded_video_{unique_id}.%(ext)s'),
                                                            'format': 'best[ext=mp4]/best',
                                                            'noplaylist': True,
                                                            'quiet': True,
                                                            'nocheckcertificate': True,
                                                            'ignoreerrors': True,
                                                            'no_warnings': True,
                                                            'force_ipv4': True,
                                                        }
                                                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                                            ydl.download([vid_url])
                                                        
                                                        # Find the downloaded file
                                                        found_path = None
                                                        for ext in ['.mp4', '.mkv', '.webm']:
                                                            possible_path = os.path.join(temp_dir, f'downloaded_video_{unique_id}{ext}')
                                                            if os.path.exists(possible_path):
                                                                found_path = possible_path
                                                                break
                                                        
                                                        if found_path:
                                                            st.session_state['downloaded_video_path'] = found_path
                                                            st.success(f"Selected video '{entry.get('title')}' fetched successfully.")
                                                            st.session_state['search_results'] = []
                                                            st.rerun()
                                                        else:
                                                            st.error("Download failed.")
                                                    except Exception as e:
                                                        st.error(f"Error downloading selected video: {e}")
            else:
                uploaded_file = st.file_uploader("Drag and drop a media file (.mp4, .mp3, .wav, etc.)", type=['mp4', 'mkv', 'avi', 'mp3', 'wav'], key="uploaded_file")
                if uploaded_file:
                    download_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(download_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    ext = os.path.splitext(download_path)[1].lower()
                    if ext in ['.mp4', '.mkv', '.avi']:
                        video_path = download_path
                        st.session_state['downloaded_video_path'] = video_path # Update session state
                    else:
                        audio_only_path = download_path
                        st.session_state['downloaded_video_path'] = None # Clear video path if audio
                    st.success(f"File uploaded: {uploaded_file.name}")

    with col_prev:
        st.markdown("#### Source Preview")
        if video_path:
            if os.path.exists(video_path):
                st.video(video_path)
            else:
                st.error("Video file not found. Please try downloading again.")
        elif audio_only_path:
            if os.path.exists(audio_only_path):
                st.audio(audio_only_path)
            else:
                st.error("Audio file not found.")
        else:
            st.info("Upload media or paste a link to see a preview.")
        
        st.markdown("---")
        st.markdown("#### ⚙️ Dubbing Settings")
        
        # Gender Selection
        gender = st.radio("Target Voice Gender", ["Female", "Male"], horizontal=True, help="Select the gender for the dubbed voice.")
        
        # Ambience / Background Audio
        mix_original = st.checkbox("Preserve Background (Ambience)", value=True, help="Keep the original audio at a lower volume to preserve background music and essence.")
        original_vol = 0.0
        if mix_original:
            original_vol = st.slider("Ambience Volume", 0.05, 0.4, 0.15, 0.05, format="%0.2f")

    
    # Action Button
    st.markdown("<hr style='border: 1px solid #3A3F50;'>", unsafe_allow_html=True)
    is_disabled = (video_path is None and audio_only_path is None)
    
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button(f"Start Dubbing to {target_lang_name}", type="primary", disabled=is_disabled, width='stretch'):
            final_input = video_path if video_path else audio_only_path
            is_vid = (video_path is not None)
            
            # Resolve Voice
            selected_voice_map = TTS_VOICE_MAP_MALE if gender == "Male" else TTS_VOICE_MAP_FEMALE
            target_voice = selected_voice_map.get(target_lang_code, tts_voice_map.get(target_lang_code))

            with st.status(f"Processing in {mode} Mode...", expanded=True) as status:
                st.write(f"Source: {source_lang_name} to Target: {target_lang_name} ({gender})")
                
                # Progress Bar
                progress_bar = st.progress(0, text="Starting pipeline...")
                
                success = False
                # Pass new args to run_pipeline: target_voice, mix_original, original_vol, progress_bar
                if mode.startswith("A"):
                    st.warning("Full Ultra mode features are simulated in this UI example. Running default pipeline.")
                    success = run_pipeline(final_input, is_vid, source_lang_code, target_lang_code, target_voice, chunk_duration_sec, base_voice_rate, base_voice_pitch, source_lang_name, target_lang_name, mode, mix_original, original_vol, progress_bar, status)
                elif mode.startswith("B"):
                    st.info("Executing Balanced pipeline...")
                    success = run_pipeline(final_input, is_vid, source_lang_code, target_lang_code, target_voice, chunk_duration_sec, base_voice_rate, base_voice_pitch, source_lang_name, target_lang_name, mode, mix_original, original_vol, progress_bar, status)
                else:
                    st.info("Executing Basic pipeline (fastest)...")
                    basic_chunk = max(15, chunk_duration_sec // 2)
                    success = run_pipeline(final_input, is_vid, source_lang_code, target_lang_code, target_voice, basic_chunk, base_voice_rate, base_voice_pitch, source_lang_name, target_lang_name, mode, mix_original, original_vol, progress_bar, status)
            
                if success:
                    progress_bar.progress(100, text="Completed!")
                    status.update(label="Dubbing Complete!", state="complete", expanded=False)
                    st.toast("Dubbing completed successfully!")
                    
                    # Save to database
                    try:
                        # Get the latest history item (just created)
                        latest_item = st.session_state['history'][-1] if st.session_state['history'] else None
                        if latest_item:
                            # Extract video info
                            video_file = os.path.basename(latest_item.get('video_path', ''))
                            title = f"Dubbed Video - {target_lang_name}"
                            description = f"Dubbed from {source_lang_name} to {target_lang_name} using {mode} mode"
                            
                            # Calculate file size and duration if available
                            file_size = 0
                            duration = 0.0
                            if latest_item.get('video_path') and os.path.exists(latest_item['video_path']):
                                file_size = os.path.getsize(latest_item['video_path'])
                                # Try to get duration from video
                                try:
                                    import cv2
                                    cap = cv2.VideoCapture(latest_item['video_path'])
                                    fps = cap.get(cv2.CAP_PROP_FPS)
                                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                                    if fps > 0:
                                        duration = frame_count / fps
                                    cap.release()
                                except:
                                    pass

                            # Save to DB
                            db.add_video_output(
                                session_id=session_id,
                                title=title,
                                description=description,
                                video_path=latest_item.get('video_path'),
                                audio_path=latest_item.get('audio_path'),
                                source_lang=source_lang_name,
                                target_lang=target_lang_name,
                                quality_mode=mode,
                                duration=duration,
                                file_size=file_size,
                                output_type='batch_studio'
                            )
                            print(f"[BatchStudio] Saved video output to database")
                    except Exception as e:
                        print(f"[BatchStudio] Failed to save video to database: {e}")
                        
                else:
                    status.update(label="Dubbing Failed", state="error", expanded=True)
                    st.toast("Dubbing failed. Check logs.", icon="❌")



    if st.session_state['history']:
        st.divider()
        
        # Initialize active video state
        if 'active_video_idx' not in st.session_state:
            st.session_state['active_video_idx'] = len(st.session_state['history']) - 1
            
        # Validate index
        if st.session_state['active_video_idx'] >= len(st.session_state['history']):
             st.session_state['active_video_idx'] = len(st.session_state['history']) - 1
        
        active_item = st.session_state['history'][st.session_state['active_video_idx']]
        
        # --- Main Player Section ---
        st.markdown("""
            <div style='text-align: center; margin-bottom: 1rem;'>
                <h2 style='
                    font-size: 1.8rem;
                    background: linear-gradient(135deg, #5B56E9 0%, #8B86FF 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: 700;
                '>🎥 Studio Player</h2>
            </div>
        """, unsafe_allow_html=True)

        if active_item.get('video_path'):
            import base64
            import re
            import streamlit.components.v1 as components
            
            # Prepare Video & Subtitles
            with open(active_item['video_path'], 'rb') as f:
                video_bytes = f.read()
            video_b64 = base64.b64encode(video_bytes).decode()
            
            vtt_b64 = ""
            if active_item.get('srt'):
                def srt_to_vtt(srt_content):
                    vtt = "WEBVTT\n\n"
                    vtt_content = re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', srt_content)
                    vtt += vtt_content
                    return vtt
                vtt_content = srt_to_vtt(active_item['srt'])
                vtt_b64 = base64.b64encode(vtt_content.encode('utf-8')).decode()

            # Custom HTML5 Player with Seek Buttons & Styled Subtitles
            video_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ margin: 0; background: transparent; font-family: 'Poppins', sans-serif; }}
                .player-container {{
                    position: relative;
                    width: 100%;
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(10, 14, 39, 0.6);
                    border-radius: 16px;
                    border: 1px solid rgba(91, 86, 233, 0.3);
                    overflow: hidden;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                }}
                video {{
                    width: 100%;
                    max-height: 500px;
                    display: block;
                    outline: none;
                }}
                /* Subtitle Styling - 1 Line, Non-obtrusive */
                video::cue {{
                    background-color: rgba(0, 0, 0, 0.6);
                    color: #fff;
                    font-size: 16px;
                    line-height: 1.5;
                    text-shadow: 1px 1px 2px black;
                    white-space: pre-wrap; 
                }}
                /* Webkit specific for line clamping if supported, otherwise rely on font size */
                video::-webkit-media-text-track-display {{
                    overflow: hidden;
                    text-overflow: ellipsis;
                    display: -webkit-box;
                    -webkit-line-clamp: 1; /* Limit to 1 line */
                    -webkit-box-orient: vertical;
                }}

                .controls {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    padding: 15px;
                    background: rgba(20, 23, 45, 0.9);
                    border-top: 1px solid rgba(91, 86, 233, 0.2);
                }}
                .btn {{
                    background: linear-gradient(135deg, #5B56E9 0%, #7B6AFF 100%);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(91, 86, 233, 0.4);
                }}
                .btn:active {{ transform: translateY(0); }}
            </style>
            </head>
            <body>
                <div class="player-container">
                    <video id="main-video" controls crossorigin="anonymous">
                        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                        {'<track label="Translated" kind="subtitles" srclang="en" src="data:text/vtt;base64,' + vtt_b64 + '" default>' if vtt_b64 else ''}
                        Your browser does not support the video tag.
                    </video>
                    <div class="controls">
                        <button class="btn" onclick="seek(-10)">⏪ -10s</button>
                        <button class="btn" onclick="seek(10)">+10s ⏩</button>
                    </div>
                </div>
                <script>
                    const video = document.getElementById('main-video');
                    
                    // Force subtitles on
                    if (video.textTracks && video.textTracks.length > 0) {{
                        video.textTracks[0].mode = 'showing';
                    }}

                    function seek(seconds) {{
                        video.currentTime += seconds;
                    }}
                </script>
            </body>
            </html>
            """
            components.html(video_html, height=600)
            
            # Download Buttons for Active Video
            c1, c2 = st.columns(2)
            with c1:
                with open(active_item['video_path'], "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="dubbed_video.mp4", mime="video/mp4", width='stretch')
            with c2:
                if active_item.get('srt'):
                    st.download_button("📄 Download Subtitles", active_item['srt'], file_name="subtitles.srt", mime="text/srt", width='stretch')

        elif active_item.get('audio_path'):
            st.audio(active_item['audio_path'])
            with open(active_item['audio_path'], "rb") as f:
                st.download_button("⬇️ Download Audio", f, file_name="dubbed_audio.wav", mime="audio/wav")

        # --- Playlist Section ---
        st.markdown("""
            <div style="margin-top: 3rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(91, 86, 233, 0.2); padding-bottom: 0.5rem;">
                <h3 style="color: #E8EAED; font-size: 1.4rem;">📺 Recent Dubs</h3>
            </div>
        """, unsafe_allow_html=True)

        for idx, item in enumerate(reversed(st.session_state['history'])):
            actual_idx = len(st.session_state['history']) - 1 - idx
            is_active = (actual_idx == st.session_state['active_video_idx'])
            
            # Card Styling
            card_bg = "rgba(91, 86, 233, 0.15)" if is_active else "rgba(30, 33, 57, 0.4)"
            border_color = "#5B56E9" if is_active else "rgba(91, 86, 233, 0.1)"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background: {card_bg};
                    border: 1px solid {border_color};
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                ">
                    <div style="font-size: 1.5rem;">{'▶️' if item.get('video_path') else '🎵'}</div>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: 600; color: #fff;">{item.get('type', 'Media')} - {item.get('timestamp', '')}</div>
                        <div style="font-size: 0.9rem; color: #A0A4B3;">
                            {item.get('source_lang', 'Unknown')} ➝ {item.get('target_lang', 'Unknown')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Play Button (Streamlit button needs to be outside HTML block to function)
                col_play, _ = st.columns([1, 5])
                with col_play:
                    if not is_active:
                        if st.button(f"Play Result #{len(st.session_state['history']) - idx}", key=f"hist_play_{idx}"):
                            st.session_state['active_video_idx'] = actual_idx
                            st.rerun()
                    else:
                        st.caption("✅ Now Playing")
