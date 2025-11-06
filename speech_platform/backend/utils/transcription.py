import azure.cognitiveservices.speech as speechsdk
import os
import structlog
from sqlalchemy.orm import Session
from models import Transcript
# import ffmpeg # No longer used
import time
import threading
from typing import Callable, Dict, Any
import asyncio
import json
import subprocess # Using subprocess for ffmpeg

logger = structlog.get_logger()

# Azure credentials from environment
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION", "centralindia")

# --- All languages from the dropdown ---
ALL_LANGUAGES = ["en-US", "en-IN", "hi-IN", "ta-IN", "te-IN", "es-ES", "fr-FR", "de-DE"]

# --- FIX: Create a 4-language list for file-based detection ---
# The SourceLanguageRecognizer (DetectAudioAtStart) has a hard limit of 4 languages.
# We will use the first 4 from the main list.
AUTO_DETECT_LANGUAGES_FILE = ["en-US", "en-IN", "hi-IN", "ta-IN"]


def normalize_audio(input_path: str) -> str:
    """
    Ensure file is PCM16 16kHz mono WAV for Azure using a direct subprocess call.
    This is more robust than the ffmpeg-python wrapper.
    """
    output_path = input_path.rsplit(".", 1)[0] + "_norm.wav"
    logger.info(f"Attempting to normalize audio: {input_path} to {output_path}")
    
    cmd = [
        'ffmpeg',
        '-i', input_path,      # Input file
        '-acodec', 'pcm_s16le', # Audio codec: PCM signed 16-bit little-endian
        '-ac', '1',             # Audio channels: 1 (mono)
        '-ar', '16k',           # Audio sample rate: 16000 Hz
        output_path,            # Output file
        '-y'                    # Overwrite output file if it exists
    ]

    try:
        # Run the command
        result = subprocess.run(
            cmd, 
            capture_output=True, # Capture stdout and stderr
            text=True, 
            check=True # Raise an error if ffmpeg returns a non-zero exit code
        )
        
        # Log ffmpeg's output for debugging, even on success
        logger.info("FFmpeg normalization successful", stdout=result.stdout, stderr=result.stderr)
        
    except subprocess.CalledProcessError as e:
        # FFmpeg failed
        logger.error(
            "FFmpeg normalization failed", 
            error=e.stderr, 
            stdout=e.stdout, 
            input=input_path
        )
        # Raise a new exception to be caught by the background task
        raise Exception(f"FFmpeg failed: {e.stderr}")
    except FileNotFoundError:
        # This error happens if 'ffmpeg' is not in the system's PATH
        logger.error("FFmpeg executable not found. Make sure it is installed and in your system's PATH.")
        raise Exception("FFmpeg executable not found.")
    except Exception as e:
        # Catch any other unexpected errors
        logger.error("An unexpected error occurred during normalization", error=str(e), input=input_path)
        raise

    return output_path

# --- FIX 1: This function was completely rewritten to *only* detect language ---
def _detect_language(normalized_path: str) -> str:
    """
    First pass: Use SourceLanguageRecognizer to quickly detect the language.
    """
    logger.info("Starting language detection pass...", file=normalized_path)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    
    # Use the 4-language list
    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=AUTO_DETECT_LANGUAGES_FILE)
    
    audio_input = None
    lang_recognizer = None
    detected_language = None

    try:
        audio_input = speechsdk.AudioConfig(filename=normalized_path)
        # Use the correct recognizer for this job
        lang_recognizer = speechsdk.SourceLanguageRecognizer(
            speech_config=speech_config,
            auto_detect_source_language_config=auto_detect_config,
            audio_config=audio_input
        )
        
        # Run detection once
        result = lang_recognizer.recognize_once()

        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            lang_result = speechsdk.AutoDetectSourceLanguageResult(result)
            detected_language = lang_result.language
            logger.info(f"Language detection successful", detected_language=detected_language)
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("Language detection NoMatch", details=result.no_match_details)
            raise Exception("Could not detect language (NoMatch).")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancel_details = result.cancellation_details
            logger.error("Language detection canceled", reason=cancel_details.reason, details=cancel_details.error_details)
            raise Exception(f"Language detection canceled: {cancel_details.error_details}")
        
    finally:
        # Explicitly delete objects to release file locks
        if lang_recognizer:
            del lang_recognizer
        if audio_input:
            del audio_input

    if not detected_language:
        raise Exception("Language detection returned empty result.")
        
    return detected_language

# --- FIX 2: This function was created, and the logic from _detect_language was moved here ---
def _transcribe_with_known_language(normalized_path: str, language: str) -> tuple[str, bool]:
    """
    Second pass: Use the detected language to get the full transcript.
    Returns (full_text, speech_was_recognized)
    """
    logger.info(f"Starting transcription pass with known language: {language}", file=normalized_path)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption, "TrueText")
    speech_config.speech_recognition_language = language # Set the language
    
    audio_input = None
    recognizer = None
    
    done = False
    full_text = []
    speech_was_recognized = False

    try:
        audio_input = speechsdk.AudioConfig(filename=normalized_path)
        # Use the correct recognizer for this job
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        def recognized(evt):
            nonlocal speech_was_recognized
            res = evt.result
            if res.reason == speechsdk.ResultReason.RecognizedSpeech:
                speech_was_recognized = True
                full_text.append(res.text)
                # This line is now correct, as 'language' is a parameter
                logger.info(f"Segment recognized ({language}): {res.text[:80]}...")
            
            elif res.reason == speechsdk.ResultReason.NoMatch:
                logger.warning(f"No speech matched for a segment. Details: {res.no_match_details}")

        def stop_cb(evt):
            nonlocal done
            logger.info(f"Recognition stopped. SessionId: {evt.session_id}")
            done = True

        def canceled(evt):
            nonlocal done
            logger.error(f"Recognition Canceled. SessionId: {evt.session_id}, Reason: {evt.reason}, Details: {evt.error_details}")
            done = True

        recognizer.recognized.connect(recognized)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(canceled)

        recognizer.start_continuous_recognition_async().get()
        while not done:
            time.sleep(0.5)
        
        recognizer.stop_continuous_recognition_async().get()
    
    finally:
        # Explicitly delete objects to release file locks
        if recognizer:
            del recognizer
        if audio_input:
            del audio_input
    
    return " ".join(full_text).strip(), speech_was_recognized


def transcribe_audio_file(session_id: int, file_path: str, language: str) -> Dict[str, Any]:
    """
    Orchestrator for transcription.
    Handles normalization, 2-pass auto-detect (if needed), and transcription.
    """
    normalized_path = None
    try:
        normalized_path = normalize_audio(file_path)
        
        final_language = language
        
        # --- This is the new 2-pass Auto-Detect logic ---
        if language == "auto":
            # This now calls the fixed function
            detected_language = _detect_language(normalized_path)
            final_language = detected_language
        # --- End 2-pass logic ---

        # Now transcribe using the *known* language
        # This call is now valid because the function exists
        transcript_text, speech_found = _transcribe_with_known_language(normalized_path, final_language)
        
        if not speech_found:
            logger.warning("No speech was recognized in the file.", file=file_path)
            transcript_text = "[No speech detected]"

        logger.info(f"✅ Full transcript length: {len(transcript_text)} chars", language=final_language)
        
        return {
            "language": final_language,
            "text": transcript_text,
            "status": "completed"
        }

    except Exception as e:
        logger.error("Transcription pipeline failed", error=str(e), file_path=file_path, exc_info=True)
        return {
            "language": language, 
            "text": f"[Transcription Error: {e}]", 
            "status": "failed"
        }
    finally:
        # Clean up the normalized file
        if normalized_path and os.path.exists(normalized_path):
            try:
                os.remove(normalized_path)
                logger.info(f"Cleaned up {normalized_path}")
            except Exception as e:
                # Log a warning but don't fail the whole task
                logger.warning(f"Could not clean up normalized file: {e}")


# --------------------------------------------------------------------------
# CONTINUOUS TRANSCRIPTION (REAL-TIME FOR WEBSOCKET)
# --------------------------------------------------------------------------

class ContinuousTranscriber:
    """
    Uses Azure Speech SDK for real-time continuous transcription.
    Expects RAW PCM audio (16kHz, 16-bit, mono).
    """
    
    def __init__(self, language: str, on_transcript: Callable, on_error: Callable):
        if not speech_key or not service_region:
            logger.error("Azure Speech configuration missing for continuous transcription.")
            raise ValueError("Azure Speech key or region not configured.")
        
        self.language = language
        self.on_transcript = on_transcript
        self.on_error = on_error
        self._running = False
        
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=service_region
            )
            
            self.audio_format = speechsdk.audio.AudioStreamFormat(16000, 16, 1)
            self.audio_stream = speechsdk.audio.PushAudioInputStream(stream_format=self.audio_format)
            self.audio_config = speechsdk.audio.AudioConfig(stream=self.audio_stream)
            
            try:
                self.speech_config.request_word_level_timestamps()
            except Exception as e:
                logger.warning(f"Could not enable word-level timestamps: {e}")
            
            # Setup language config
            if language == "auto":
                # --- NOTE: Continuous streaming (websocket) CAN use all languages ---
                self.auto_lang_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                    languages=ALL_LANGUAGES
                )
                self.recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    auto_detect_source_language_config=self.auto_lang_config,
                    audio_config=self.audio_config
                )
            else:
                self.speech_config.speech_recognition_language = language
                self.recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    audio_config=self.audio_config
                )
            
            # Connect event handlers
            self.recognizer.recognizing.connect(self.on_recognizing)
            self.recognizer.recognized.connect(self.on_recognized)
            self.recognizer.session_stopped.connect(self.on_session_stopped)
            self.recognizer.canceled.connect(self.on_canceled)
            
            logger.info(f"✅ ContinuousTranscriber initialized for language: {language}")
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize SpeechRecognizer: {e}")
            self.on_error(f"Failed to initialize SpeechRecognizer: {e}")
            raise
    
    def _get_result_data(self, evt: speechsdk.SpeechRecognitionEventArgs, is_final: bool) -> dict:
        """Helper to extract data from recognition event."""
        text = evt.result.text
        if not text:
            return None
        
        confidence = 0.0
        display_text = text
        
        try:
            json_str = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
            if json_str:
                json_result = json.loads(json_str)
                confidence = json_result.get("Confidence", 0.0)
                display_text = json_result.get("DisplayText", text)
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not parse JSON result: {e}")
        
        detected_lang = self.language
        if self.language == "auto":
            try:
                lang_result = speechsdk.AutoDetectSourceLanguageResult(evt.result)
                detected_lang = lang_result.language
            except Exception:
                detected_lang = "unknown"
        
        data = {
            "type": "transcript",
            "is_final": is_final,
            "text": display_text,
            "confidence": confidence,
            "language": detected_lang,
        }
        
        return data
    
    def on_recognizing(self, evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            data = self._get_result_data(evt, is_final=False)
            if data:
                self.on_transcript(data)
    
    def on_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            data = self._get_result_data(evt, is_final=True)
            if data:
                logger.info(f"✅ Final transcript: {data['text']}")
                self.on_transcript(data)
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logger.debug("⚠️ No speech recognized in this segment.")
    
    def on_session_stopped(self, evt: speechsdk.SessionEventArgs):
        logger.info("Recognition session stopped.")
        self._running = False
    
    def on_canceled(self, evt: speechsdk.SpeechRecognitionCanceledEventArgs):
        logger.error(f"❌ Recognition canceled: {evt.reason}")
        error_message = f"Recognition error: {evt.reason}"
        
        if evt.reason == speechsdk.CancellationReason.Error:
            error_details = evt.error_details if hasattr(evt, 'error_details') else "Unknown error"
            error_message += f" - {error_details}"
            logger.error(f"Error details: {error_details}")
        
        self._running = False
        self.on_error(error_message)
    
    def start(self):
        try:
            self.recognizer.start_continuous_recognition_async().get()
            self._running = True
            logger.info("✅ Continuous recognition started")
        except Exception as e:
            logger.error(f"❌ Failed to start recognition: {e}")
            self.on_error(f"Failed to start recognition: {e}")
    
    def stop(self):
        if self._running:
            try:
                self.recognizer.stop_continuous_recognition_async().get()
            except Exception as e:
                logger.error(f"Error stopping recognizer: {e}")
            finally:
                self._running = False
                try:
                    self.audio_stream.close()
                except Exception as e:
                    logger.warning(f"Error closing audio stream: {e}")
    
    def push_audio(self, audio_chunk: bytes):
      if isinstance(audio_chunk, memoryview):
        audio_chunk = audio_chunk.tobytes()
      elif isinstance(audio_chunk, bytearray):
         audio_chunk = bytes(audio_chunk)
      
      if not self._running:
          logger.warning("Attempted to push audio to a stopped transcriber.")
          return
          
      try:
        self.audio_stream.write(audio_chunk)
      except TypeError as e:
        logger.error(f"TypeError in push_audio: {e}. Expected bytes, got {type(audio_chunk)}")
        self.on_error(f"Audio stream error: {e}")
        self.stop()
      except Exception as e:
        logger.error(f"Failed to write audio chunk: {e}")
        self.on_error(f"Audio stream error: {e}")
        self.stop()

    def __del__(self):
        try:
            if hasattr(self, 'audio_stream'):
                self.audio_stream.close()
            if hasattr(self, 'recognizer'):
                self.recognizer.recognizing.disconnect_all()
                self.recognizer.recognized.disconnect_all()
                self.recognizer.session_stopped.disconnect_all()
                self.recognizer.canceled.disconnect_all()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")