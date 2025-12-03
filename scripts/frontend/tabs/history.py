import streamlit as st
import pandas as pd
from scripts.backend.db import DatabaseManager

def render_history(target_lang_name, source_lang_name, mode):
    st.markdown("## 📂 Session History & Downloads")
    
    db = DatabaseManager()
    session_id = st.session_state.get('session_id')
    
    # Get both video outputs and dubbing history
    video_outputs = db.get_video_outputs(session_id)
    history_items = db.get_history(session_id)
    
    # Create tabs for different history views
    tab1, tab2 = st.tabs(["📹 Video Outputs", "📚 Dubbing History"])
    
    with tab1:
        if not video_outputs:
            st.info("No video outputs found. Process videos in Batch Studio to see them here.")
        else:
            st.caption(f"**{len(video_outputs)}** processed videos in your session")
            
            for idx, video in enumerate(video_outputs):
                import os
                
                # Format file size
                file_size_mb = video['file_size'] / (1024 * 1024) if video['file_size'] else 0
                duration_min = video['duration'] / 60 if video['duration'] else 0
                
                with st.expander(
                    f"**{video['title']}** | {video['timestamp']}", 
                    expanded=(idx == 0)
                ):
                    col_info, col_media = st.columns([1, 2])
                    
                    with col_info:
                        st.markdown("#### Video Information")
                        st.write(f"**Description:** {video['description']}")
                        st.metric("Quality Mode", video['quality_mode'])
                        st.metric("Languages", f"{video['source_lang']} → {video['target_lang']}")
                        
                        if duration_min > 0:
                            st.metric("Duration", f"{duration_min:.1f} min")
                        if file_size_mb > 0:
                            st.metric("File Size", f"{file_size_mb:.1f} MB")
                        
                        st.markdown("---")
                        st.markdown("#### Downloads")
                        
                        # Download buttons
                        if video['video_path'] and os.path.exists(video['video_path']):
                            with open(video['video_path'], "rb") as f:
                                st.download_button(
                                    "📥 Download Video",
                                    f,
                                    file_name=f"{video['title']}.mp4",
                                    key=f"vid_{idx}",
                                    width='stretch'
                                )
                        
                        if video['audio_path'] and os.path.exists(video['audio_path']):
                            with open(video['audio_path'], "rb") as f:
                                st.download_button(
                                    "🎵 Download Audio",
                                    f,
                                    file_name=f"{video['title']}.wav",
                                    key=f"aud_{idx}",
                                    width='stretch'
                                )
                    
                    with col_media:
                        st.markdown("#### Preview")
                        if video['video_path'] and os.path.exists(video['video_path']):
                            st.video(video['video_path'])
                        elif video['audio_path'] and os.path.exists(video['audio_path']):
                            st.audio(video['audio_path'])
                        else:
                            st.warning("Media file not found (might have been cleaned up).")
    
    with tab2:
        if not history_items:
            st.info("No dubbing tasks found in history.")
        else:
            for idx, item in enumerate(history_items):
                # Use the stored target language if available, otherwise fallback to current selection
                display_target = item.get('target_lang', target_lang_name)
                
                # Calculate reverse index for display (Task #N)
                task_num = len(history_items) - idx
                
                with st.expander(f"**Task #{task_num}** | {item['timestamp']} - {item['type']} to {display_target}", expanded=(idx == 0)):
                    col_det, col_prev = st.columns([1, 2])
                    
                    with col_det:
                        st.markdown("#### Task Details")
                        st.metric("Source Lang", item.get('source_lang', 'N/A'))
                        st.metric("Target Lang", item.get('target_lang', 'N/A'))
                        st.metric("Mode Used", item.get('mode', 'N/A'))
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### Downloads")
                        
                        # Verify file existence before showing download button
                        import os
                        
                        if item.get('video_path') and os.path.exists(item['video_path']):
                            with open(item['video_path'], "rb") as f:
                                st.download_button(f"Download Video 🎬", f, file_name=f"video_{task_num}.mp4", key=f"v_{idx}_hist", type="secondary", width='stretch')
                        
                        if item.get('audio_path') and os.path.exists(item['audio_path']):
                            with open(item['audio_path'], "rb") as f:
                                st.download_button(f"Download Audio 🎧", f, file_name=f"audio_{task_num}.wav", key=f"a_{idx}_hist", type="secondary", width='stretch')

                        if item.get('srt'):
                            st.download_button(f"Download Subtitles 📄", item['srt'], file_name=f"subs_{task_num}.srt", key=f"s_{idx}_hist", type="secondary", width='stretch')

                        if item.get('segments'):
                            # Prepare CSV data
                            csv_data = []
                            for seg in item['segments']:
                                csv_data.append({
                                    "ID": item.get('id', 'N/A'),
                                    "Transcript": seg.get('original', ''),
                                    "Translation": seg.get('translated', ''),
                                    "Confidence": f"{seg.get('confidence', 0.0):.2f}",
                                    "Start": f"{seg.get('start', 0.0):.2f}s",
                                    "End": f"{seg.get('end', 0.0):.2f}s"
                                })
                            
                            if csv_data:
                                df_export = pd.DataFrame(csv_data)
                                csv_string = df_export.to_csv(index=False).encode('utf-8-sig')
                                st.download_button(
                                    label="Download Analysis CSV 📊",
                                    data=csv_string,
                                    file_name=f"analysis_{task_num}.csv",
                                    mime="text/csv",
                                    key=f"csv_{idx}_hist",
                                    type="secondary",
                                    width='stretch'
                                )

                    with col_prev:
                        st.markdown("#### Preview")
                        if item.get('video_path') and os.path.exists(item['video_path']):
                            st.video(item['video_path'])
                        elif item.get('audio_path') and os.path.exists(item['audio_path']):
                            st.audio(item['audio_path'])
                        else:
                            st.warning("Media file not found (might have been cleaned up).")
