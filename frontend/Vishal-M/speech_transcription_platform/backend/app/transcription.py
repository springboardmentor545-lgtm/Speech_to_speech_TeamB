import azure.cognitiveservices.speech as speechsdk
import asyncio
from typing import Dict, Optional
from .config import get_settings
from .logger import get_logger


settings = get_settings()
logger = get_logger(__name__)


class TranscriptionService:
    def __init__(self):
        self.speech_key = settings.SPEECH_KEY
        self.service_region = settings.SERVICE_REGION
        # Limit languages to English and Hindi
        self.auto_detect_config = speechsdk.AutoDetectSourceLanguageConfig(
            languages=["en-US", "hi-IN"]
        )


    def _get_speech_config(self) -> speechsdk.SpeechConfig:
        config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.service_region
        )
        config.speech_recognition_language = "en-US"
        return config


    async def transcribe_file(self, file_path: str) -> Dict[str, str]:
        """
        Transcribe entire audio file using continuous recognition.
        This will capture all speech in the file, not just the first utterance.
        """
        try:
            logger.info("transcription_started", file_path=file_path)

            speech_config = self._get_speech_config()
            audio_config = speechsdk.AudioConfig(filename=file_path)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                auto_detect_source_language_config=self.auto_detect_config,
                audio_config=audio_config
            )

            # Storage for transcription results
            all_results = []
            done = asyncio.Event()
            detected_language = "unknown"

            def recognized_handler(evt):
                nonlocal detected_language
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    try:
                        auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(evt.result)
                        detected_language = auto_detect_result.language
                        all_results.append(evt.result.text)
                        logger.info(
                            "partial_transcription",
                            language=detected_language,
                            text=evt.result.text
                        )
                    except Exception as e:
                        logger.warning("language_detection_failed", error=str(e))
                        all_results.append(evt.result.text)

            def session_stopped_handler(evt):
                logger.info("transcription_session_stopped", file_path=file_path)
                done.set()

            def canceled_handler(evt):
                logger.warning("transcription_canceled", reason=str(evt.reason))
                done.set()

            # Connect event handlers
            recognizer.recognized.connect(recognized_handler)
            recognizer.session_stopped.connect(session_stopped_handler)
            recognizer.canceled.connect(canceled_handler)

            # Start continuous recognition
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, recognizer.start_continuous_recognition)

            # Wait until transcription is complete (with timeout)
            try:
                await asyncio.wait_for(done.wait(), timeout=3600.0)  # 1 hour timeout
            except asyncio.TimeoutError:
                logger.warning("transcription_timeout", file_path=file_path)

            # Stop recognition
            await loop.run_in_executor(None, recognizer.stop_continuous_recognition)

            # Combine all results
            full_transcript = " ".join(all_results).strip()

            if full_transcript:
                logger.info(
                    "transcription_completed",
                    language=detected_language,
                    text_length=len(full_transcript),
                    segments=len(all_results)
                )
                return {
                    "language": detected_language,
                    "text": full_transcript,
                    "status": "completed",
                    "segments": len(all_results)
                }
            else:
                logger.warning("no_speech_detected", file_path=file_path)
                return {
                    "language": "unknown",
                    "text": "",
                    "status": "no_speech",
                    "error": "No speech detected in audio"
                }

        except Exception as e:
            logger.error("transcription_exception", error=str(e), file_path=file_path)
            return {
                "language": "unknown",
                "text": "",
                "status": "failed",
                "error": str(e)
            }


    async def recognize_from_stream(
        self,
        stream: speechsdk.audio.PushAudioInputStream
    ) -> Dict[str, str]:
        """
        Recognize from audio stream using continuous recognition.
        """
        try:
            speech_config = self._get_speech_config()
            audio_config = speechsdk.audio.AudioConfig(stream=stream)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                auto_detect_source_language_config=self.auto_detect_config,
                audio_config=audio_config
            )

            all_results = []
            done = asyncio.Event()
            detected_language = "unknown"

            def recognized_handler(evt):
                nonlocal detected_language
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    try:
                        auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(evt.result)
                        detected_language = auto_detect_result.language
                        all_results.append(evt.result.text)
                    except Exception:
                        all_results.append(evt.result.text)

            def session_stopped_handler(evt):
                done.set()

            recognizer.recognized.connect(recognized_handler)
            recognizer.session_stopped.connect(session_stopped_handler)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, recognizer.start_continuous_recognition)

            try:
                await asyncio.wait_for(done.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                pass

            await loop.run_in_executor(None, recognizer.stop_continuous_recognition)

            full_transcript = " ".join(all_results).strip()

            if full_transcript:
                return {
                    "language": detected_language,
                    "text": full_transcript,
                    "status": "completed"
                }

            return {
                "language": "unknown",
                "text": "",
                "status": "no_speech"
            }

        except Exception as e:
            logger.error("stream_recognition_failed", error=str(e))
            return {
                "language": "unknown",
                "text": "",
                "status": "failed",
                "error": str(e)
            }


    async def recognize_continuous(
        self,
        stream: speechsdk.audio.PushAudioInputStream,
        callback
    ):
        """
        Real-time continuous recognition with callback for each recognized phrase.
        Use this for live streaming scenarios.
        """
        try:
            speech_config = self._get_speech_config()
            audio_config = speechsdk.audio.AudioConfig(stream=stream)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                auto_detect_source_language_config=self.auto_detect_config,
                audio_config=audio_config
            )

            loop = asyncio.get_event_loop()

            def recognized_handler(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    try:
                        auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(evt.result)
                        asyncio.run_coroutine_threadsafe(
                            callback({
                                "language": auto_detect_result.language,
                                "text": evt.result.text,
                                "status": "recognized"
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.warning("callback_failed", error=str(e))

            def canceled_handler(evt):
                logger.warning("continuous_recognition_canceled", reason=str(evt.reason))

            recognizer.recognized.connect(recognized_handler)
            recognizer.canceled.connect(canceled_handler)

            await loop.run_in_executor(None, recognizer.start_continuous_recognition)

            return recognizer

        except Exception as e:
            logger.error("continuous_recognition_setup_failed", error=str(e))
            raise


transcription_service = TranscriptionService()
