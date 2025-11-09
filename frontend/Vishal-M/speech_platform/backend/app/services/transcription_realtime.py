# speech_platform/services/transcription_realtime.py
import azure.cognitiveservices.speech as speechsdk
import os
import structlog
import time
import threading
from typing import Callable, Dict, Any
import asyncio
import json

logger = structlog.get_logger()

# Azure credentials from environment
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION", "centralindia")

# --- All languages from the dropdown ---
ALL_LANGUAGES = ["en-US", "en-IN", "hi-IN", "ta-IN", "te-IN", "es-ES", "fr-FR", "de-DE"]

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
        
        return {
            "type": "transcript",
            "is_final": is_final,
            "text": display_text,
            "confidence": confidence,
            "language": detected_lang,
        }
    
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