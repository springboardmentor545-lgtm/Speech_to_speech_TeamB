# speech_platform/services/transcription_file.py
import azure.cognitiveservices.speech as speechsdk
import os
import structlog
import time
import subprocess
from typing import Dict, Any

logger = structlog.get_logger()

# Azure credentials from environment
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION", "centralindia")

# --- FIX: Create a 4-language list for file-based detection ---
# The SourceLanguageRecognizer (DetectAudioAtStart) has a hard limit of 4 languages.
AUTO_DETECT_LANGUAGES_FILE = ["en-US", "en-IN", "hi-IN", "ta-IN"]

def normalize_audio(input_path: str) -> str:
    """
    Ensure file is PCM16 16kHz mono WAV for Azure using a direct subprocess call.
    """
    supported_formats = ['.wav', '.mp3', '.ogg', '.flac', '.aiff', '.au']
    file_ext = os.path.splitext(input_path)[1].lower()
    
    if file_ext in supported_formats and file_ext == '.wav':
        logger.info(f"File is already in WAV format, skipping normalization: {input_path}")
        return input_path
    
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
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        logger.info("FFmpeg normalization successful", stdout=result.stdout, stderr=result.stderr)
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(
            "FFmpeg normalization failed", 
            error=e.stderr, 
            stdout=e.stdout, 
            input=input_path
        )
        if file_ext in supported_formats:
            logger.warning("Falling back to original audio file without normalization")
            return input_path
        else:
            raise Exception(f"Cannot process {file_ext} format without FFmpeg.")
    except FileNotFoundError:
        logger.warning("FFmpeg executable not found.")
        if file_ext in supported_formats:
            logger.warning("Using original file without normalization.")
            return input_path
        else:
            raise Exception(f"FFmpeg is required to convert {file_ext} format.")
    except Exception as e:
        logger.error("An unexpected error occurred during normalization", error=str(e), input=input_path)
        if file_ext in supported_formats:
            logger.warning("Falling back to original audio file without normalization")
            return input_path
        else:
            raise Exception(f"Cannot process {file_ext} format. Error: {str(e)}")

def _detect_language(normalized_path: str) -> str:
    """
    First pass: Use SourceLanguageRecognizer to quickly detect the language.
    """
    logger.info("Starting language detection pass...", file=normalized_path)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=AUTO_DETECT_LANGUAGES_FILE)
    
    audio_input = None
    lang_recognizer = None
    detected_language = None
    try:
        audio_input = speechsdk.AudioConfig(filename=normalized_path)
        lang_recognizer = speechsdk.SourceLanguageRecognizer(
            speech_config=speech_config,
            auto_detect_source_language_config=auto_detect_config,
            audio_config=audio_input
        )
        result = lang_recognizer.recognize_once()

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
        if lang_recognizer: del lang_recognizer
        if audio_input: del audio_input

    if not detected_language:
        raise Exception("Language detection returned empty result.")
    return detected_language

def _transcribe_with_known_language(normalized_path: str, language: str) -> tuple[str, bool]:
    """
    Second pass: Use the detected language to get the full transcript.
    Returns (full_text, speech_was_recognized)
    """
    logger.info(f"Starting transcription pass with known language: {language}", file=normalized_path)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption, "TrueText")
    speech_config.speech_recognition_language = language
    
    audio_input = None
    recognizer = None
    done = False
    full_text = []
    speech_was_recognized = False

    try:
        audio_input = speechsdk.AudioConfig(filename=normalized_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        def recognized(evt):
            nonlocal speech_was_recognized
            res = evt.result
            if res.reason == speechsdk.ResultReason.RecognizedSpeech:
                speech_was_recognized = True
                full_text.append(res.text)
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
        if recognizer: del recognizer
        if audio_input: del audio_input
    
    return " ".join(full_text).strip(), speech_was_recognized


def transcribe_audio_file(session_id: int, file_path: str, language: str) -> Dict[str, Any]:
    """
    Orchestrator for transcription.
    """
    normalized_path = None
    try:
        normalized_path = normalize_audio(file_path)
        final_language = language
        
        if language == "auto":
            detected_language = _detect_language(normalized_path)
            final_language = detected_language

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
        if normalized_path and os.path.exists(normalized_path):
            try:
                os.remove(normalized_path)
                logger.info(f"Cleaned up {normalized_path}")
            except Exception as e:
                logger.warning(f"Could not clean up normalized file: {e}")