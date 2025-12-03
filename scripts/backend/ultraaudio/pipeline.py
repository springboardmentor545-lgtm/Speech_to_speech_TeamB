import os
import time
import tempfile
import shutil
import uuid
import gc

import moviepy.editor as mp
import concurrent.futures
import azure.cognitiveservices.speech as speechsdk
import streamlit as st
import threading
import wave
from datetime import datetime
import json
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

try:
    import noisereduce as nr
    import soundfile as sf
except Exception as e:
    print(f"DEBUG: Failed to import noisereduce or soundfile: {e}")
    nr = None
    sf = None

from .config import get_azure_configs
from .srt_utils import generate_srt_content


def split_audio(audio_path, chunk_duration_sec, temp_dir):
    try:
        audio = mp.AudioFileClip(audio_path)
        total_duration = audio.duration
        chunk_paths = []
        for i, start_time in enumerate(range(0, int(total_duration) + 1, chunk_duration_sec)):
            end_time = min(start_time + chunk_duration_sec, total_duration)
            if start_time >= end_time:
                continue
            chunk_path = os.path.join(temp_dir, f"chunk_{i}.wav")
            try:
                sub_audio = audio.subclip(start_time, end_time)
                sub_audio.write_audiofile(
                    chunk_path, codec='pcm_s16le', fps=16000, nbytes=2,
                    ffmpeg_params=["-ac", "1"], logger=None
                )
                chunk_paths.append((chunk_path, i, start_time))
            except Exception:
                pass
        return chunk_paths
    finally:
        try:
            audio.close()
        except:
            pass


def recognize_chunk(task_data):
    chunk_path, chunk_index, target_lang_code, translation_config = task_data
    audio_input = speechsdk.AudioConfig(filename=chunk_path)
    translator = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_input
    )
    translator.add_target_language(target_lang_code)
    segments = []
    rec_text_parts = []
    trans_text_parts = []
    done = threading.Event() if 'threading' in globals() else None

    def handle_translation(evt):
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            start_sec = evt.result.offset / 10_000_000
            duration_sec = evt.result.duration / 10_000_000
            trans = evt.result.translations[target_lang_code]
            segments.append({
                'start': start_sec,
                'duration': duration_sec,
                'original': evt.result.text,
                'translated': trans
            })
            rec_text_parts.append(evt.result.text)
            trans_text_parts.append(trans)

    translator.recognized.connect(handle_translation)
    if done is not None:
        translator.session_stopped.connect(lambda evt: done.set())
    translator.start_continuous_recognition_async()
    if done is not None:
        done.wait(timeout=200)
    translator.stop_continuous_recognition_async().get()
    return (chunk_index, segments, " ".join(rec_text_parts), " ".join(trans_text_parts))


def synthesize_segment_ssml(segment_data):
    i, segment, synthesis_config, temp_dir, rate, pitch, voice_name = segment_data
    text = segment.get('translated', '')
    start_time = segment.get('start', 0)
    if not text or text.isspace():
        return None
    path = os.path.join(temp_dir, f"seg_{i}.wav")

    ssml_string = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{voice_name}">
            <prosody rate="{rate}" pitch="{pitch}">
                {text}
            </prosody>
        </voice>
    </speak>
    """
    try:
        audio_cfg = speechsdk.audio.AudioOutputConfig(filename=path)
        syn = speechsdk.SpeechSynthesizer(speech_config=synthesis_config, audio_config=audio_cfg)
        res = syn.speak_ssml_async(ssml_string).get()

        if res.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if os.path.exists(path) and os.path.getsize(path) > 44:
                return (path, start_time)
        return None
    except Exception:
        return None


def resolve_audio_overlaps(clip_data_list):
    if not clip_data_list:
        return []
    sorted_data = sorted(clip_data_list, key=lambda x: x[1])

    final_clips = []
    last_end_time = 0.0

    for path, start_time in sorted_data:
        try:
            clip = mp.AudioFileClip(path)
            duration = clip.duration

            if start_time < last_end_time:
                new_start = last_end_time + 0.05
                clip = clip.set_start(new_start)
                last_end_time = new_start + duration
            else:
                clip = clip.set_start(start_time)
                last_end_time = start_time + duration

            final_clips.append(clip)
        except Exception:
            pass

    return final_clips


def run_pipeline(
    input_path, 
    is_video, 
    source_lang_code, 
    target_lang_code, 
    voice_name, 
    chunk_duration, 
    voice_rate, 
    voice_pitch, 
    source_lang_name, 
    target_lang_name, 
    mode,
    mix_original=False,
    original_vol=0.0,
    progress_bar=None,
    status_container=None
):
    # Fetch Azure credentials
    speech_key, service_region = get_azure_configs()
    
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=speech_key, 
        region=service_region
    )
    translation_config.speech_recognition_language = source_lang_code
    translation_config.add_target_language(target_lang_code)

    synthesis_config = speechsdk.SpeechConfig(
        subscription=speech_key, 
        region=service_region
    )
    synthesis_config.speech_synthesis_voice_name = voice_name
    temp_audio_path = None
    all_segments = []
    resources = []
    total_duration = 0

    try:
        # 1. Extract Audio + Optional Noise Reduction
        if status_container:
            status_container.write("Step 1/3: Processing audio source...")
        
        if is_video:
            media_clip = mp.VideoFileClip(input_path)
            audio_clip = media_clip.audio
            resources.append(media_clip)
        else:
            media_clip = mp.AudioFileClip(input_path)
            audio_clip = media_clip
            resources.append(media_clip)
        
        total_duration = media_clip.duration

        temp_audio_path = os.path.join(st.session_state['temp_dir'], "process_audio.wav")
        audio_clip.write_audiofile(
            temp_audio_path, codec='pcm_s16le', fps=16000,
            nbytes=2, ffmpeg_params=["-ac", "1"], logger=None
        )

        # Noise reduction
        try:
            if nr is not None and sf is not None:
                data, sr = sf.read(temp_audio_path)
                reduced_noise = nr.reduce_noise(y=data, sr=sr)
                clean_path = os.path.join(st.session_state['temp_dir'], "clean_audio.wav")
                sf.write(clean_path, reduced_noise, sr)
                temp_audio_path = clean_path
                print("✅ Noise reduction applied")
            else:
                print("noisereduce or soundfile not available; skipping denoise")
        except Exception as e:
            print(f"Noise reduction failed: {e}")

        # 2. Stream Recognize & Incremental Synthesize (low-latency)
        if status_container:
            status_container.write("Step 2/3: Recognizing and synthesizing...")

        def stream_recognize_and_synthesize(wav_path, translation_config, synthesis_config,
                                            target_lang, voice_name, temp_dir,
                                            voice_rate_local, voice_pitch_local):
            """Recognize and synthesize audio from a file using Azure SDK's file input.
            
            Returns (all_segments, translated_clip_paths)
            """

            all_segs = []
            translated_paths = []
            # Use sequential execution to prevent 'bad allocation' errors in Azure SDK
            synth_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            synth_futures = []
            seq_lock = threading.Lock()
            seq_counter = {'v': 0}

            # Use file-based AudioConfig for faster-than-realtime processing
            audio_config = speechsdk.audio.AudioConfig(filename=wav_path)

            recognizer = speechsdk.translation.TranslationRecognizer(
                translation_config=translation_config,
                audio_config=audio_config
            )
            recognizer.add_target_language(target_lang)

            done = threading.Event()
            
            start_time_perf = time.time()
            
            # Capture the current Streamlit context
            ctx = get_script_run_ctx()

            def on_translated(evt):
                # Attach the context to this thread
                if ctx:
                    add_script_run_ctx(threading.current_thread(), ctx)
                    
                try:
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        # Debug: Print available translations
                        # print(f"DEBUG: Available translations: {evt.result.translations.keys()}")
                        
                        if target_lang not in evt.result.translations:
                            print(f"WARNING: Target language '{target_lang}' not found in translations.")
                            return

                        start_sec = getattr(evt.result, 'offset', 0) / 10_000_000
                        duration_sec = getattr(evt.result, 'duration', 0) / 10_000_000
                        translated_text = evt.result.translations[target_lang]
                        original_text = evt.result.text
                        
                        # Progress Update
                        if progress_bar and total_duration > 0:
                            current_pos = start_sec + duration_sec
                            progress = min(current_pos / total_duration, 1.0)
                            
                            # Estimate Time Remaining
                            elapsed = time.time() - start_time_perf
                            if progress > 0.01:
                                total_estimated = elapsed / progress
                                remaining = total_estimated - elapsed
                                etr_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                            else:
                                etr_str = "Calculating..."
                                
                            progress_bar.progress(progress, text=f"Translating: {int(progress*100)}% | Est. Remaining: {etr_str}")

                        # Try to extract confidence
                        confidence = 0.0
                        try:
                            json_res = json.loads(evt.result.json)
                            if 'NBest' in json_res and len(json_res['NBest']) > 0:
                                confidence = json_res['NBest'][0].get('Confidence', 0.0) * 100
                        except Exception as json_err:
                            print(f"DEBUG: JSON parse error (ignoring): {json_err}")
                            pass

                        trans_time_iso = datetime.now().isoformat()

                        seg = {
                            'start': start_sec,
                            'duration': duration_sec,
                            'original': original_text,
                            'translated': translated_text,
                            'confidence': confidence,
                            'input_time': start_sec,
                            'translation_time': trans_time_iso,
                            'output_time': None
                        }
                        all_segs.append(seg)

                        # schedule synthesis immediately
                        with seq_lock:
                            sid = seq_counter['v']
                            seq_counter['v'] += 1

                        # Dynamic Speed Adjustment
                        char_density = len(translated_text) / (duration_sec + 0.1) # avoid div by zero
                        
                        try:
                            base_rate_val = int(voice_rate_local.strip('%'))
                        except:
                            base_rate_val = 0
                        
                        dynamic_boost = 0
                        if char_density > 20:
                            dynamic_boost = int((char_density - 20) * 5)
                            dynamic_boost = min(dynamic_boost, 50)
                        
                        final_rate = f"{base_rate_val + dynamic_boost}%"
                        if base_rate_val + dynamic_boost > 0:
                            final_rate = f"+{final_rate}"

                        def synth_task(sid_local, seg_local, rate_local):
                            text = seg_local.get('translated', '')
                            if not text or text.isspace():
                                return None

                            ssml = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<voice name="{voice_name}">
<prosody rate="{rate_local}" pitch="{voice_pitch_local}">{text}</prosody>
</voice>
</speak>
"""
                            syn = None
                            try:
                                # Create a fresh synthesizer for each segment to avoid state issues
                                # Use os.devnull to prevent trying to open default speaker on server
                                null_audio_config = speechsdk.audio.AudioConfig(filename=os.devnull)
                                syn = speechsdk.SpeechSynthesizer(speech_config=synthesis_config, audio_config=null_audio_config)
                                res = syn.speak_ssml_async(ssml).get()
                                
                                if res.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                    out_path = os.path.join(temp_dir, f"seg_stream_{sid_local}.wav")
                                    try:
                                        # Write the audio data to file manually
                                        with open(out_path, 'wb') as f:
                                            f.write(res.audio_data)
                                        
                                        # Update output time
                                        seg_local['output_time'] = datetime.now().isoformat()
                                        
                                        return (out_path, seg_local.get('start', 0))
                                    except Exception as write_err:
                                        print(f"DEBUG: Failed to write audio file: {write_err}")
                                        return None
                                else:
                                    return None
                            except Exception as e:
                                print(f"Synthesis exception: {e}")
                                return None
                            finally:
                                if syn:
                                    del syn

                        fut = synth_executor.submit(synth_task, sid, seg, final_rate)
                        synth_futures.append(fut)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Translation event handler error: {e}")

            def on_canceled(evt):
                if evt.result.reason == speechsdk.ResultReason.Canceled:
                    details = evt.result.cancellation_details
                    if details.reason == speechsdk.CancellationReason.EndOfStream:
                        pass
                    else:
                        print(f"ERROR: Recognition canceled. Reason: {details.reason}")
                done.set()

            recognizer.recognized.connect(on_translated)
            recognizer.canceled.connect(on_canceled)
            recognizer.session_stopped.connect(lambda evt: done.set())

            # start recognition
            recognizer.start_continuous_recognition_async()

            # Wait for the file to be fully processed
            done.wait()

            # stop recognition
            recognizer.stop_continuous_recognition_async()

            # wait for synthesis futures
            for sf in concurrent.futures.as_completed(synth_futures):
                try:
                    r = sf.result()
                    if r:
                        translated_paths.append(r)
                except Exception as e:
                    print(f"Synthesis future exception: {e}")
            
            synth_executor.shutdown(wait=True)
            return all_segs, translated_paths

        all_segments, translated_clip_paths = stream_recognize_and_synthesize(
            temp_audio_path, translation_config, synthesis_config,
            target_lang_code, voice_name, st.session_state['temp_dir'],
            voice_rate, voice_pitch
        )

        # 3. Assemble Final Audio
        if status_container:
            status_container.write("Step 3/3: Assembling final video...")
        
        if progress_bar:
            progress_bar.progress(90, text="Rendering final video (this may take a moment)...")

        translated_audio_clips = resolve_audio_overlaps(translated_clip_paths)
        
        if not translated_audio_clips:
            st.error("No audio segments were generated. Check logs.")
            return False

        final_audio = mp.CompositeAudioClip(translated_audio_clips)
        resources.extend(translated_audio_clips)
        
        # Ensure final audio matches video duration (or slightly longer)
        final_end = 0
        if translated_audio_clips:
            c = translated_audio_clips[-1]
            final_end = max(getattr(c, "end", 0) for c in translated_audio_clips)
        final_audio.duration = max(getattr(media_clip, "duration", 0), final_end)

        # --- Ambience Mixing ---
        if mix_original and is_video:
            try:
                # Get original audio
                original_audio = media_clip.audio
                # Lower volume
                original_audio = original_audio.volumex(original_vol)
                # Mix
                final_audio = mp.CompositeAudioClip([original_audio, final_audio])
                # Ensure duration is correct (use original video duration as base)
                final_audio.duration = media_clip.duration
            except Exception as e:
                print(f"Ambience mixing failed: {e}")
        # -----------------------

        # Generate unique ID for this run
        run_id = str(uuid.uuid4())[:6]
        
        final_audio_path = os.path.join(st.session_state['temp_dir'], f"final_output_{run_id}.wav")
        final_audio.write_audiofile(final_audio_path, codec='pcm_s16le', fps=16000, logger=None)

        srt_content = generate_srt_content(all_segments)

        result_data = {
            "id": run_id,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": "Video" if is_video else "Audio",
            "srt": srt_content,
            "audio_path": final_audio_path,
            "video_path": None,
            "original_path": input_path if is_video else None,
            "filename": os.path.basename(input_path) if input_path else "unknown",
            "segments": all_segments,
            "source_lang": source_lang_name,
            "target_lang": target_lang_name,
            "mode": mode
        }

        if is_video:
            final_vid_path = os.path.join(st.session_state['temp_dir'], f"final_video_{run_id}.mp4")
            new_audio = mp.AudioFileClip(final_audio_path)
            resources.append(new_audio)

            final_video = media_clip.set_audio(new_audio)
            resources.append(final_video)

            final_video.write_videofile(
                final_vid_path, codec='libx264',
                audio_codec='aac', logger=None
            )
            result_data["video_path"] = final_vid_path

        # Save to DB
        from scripts.backend.db import DatabaseManager
        try:
            db = DatabaseManager()
            session_id = st.session_state.get('session_id')
            db.add_history_item(result_data, session_id)
        except Exception as e:
            print(f"DB Save Error: {e}")

        st.session_state['history'].append(result_data)
        
        # Cleanup resources
        for r in resources:
            try:
                if hasattr(r, 'close'):
                    r.close()
            except:
                pass
        
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        st.error(f"Pipeline Error: {e}")
        return False
    finally:
        pass
