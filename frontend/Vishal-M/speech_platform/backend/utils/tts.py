import azure.cognitiveservices.speech as speechsdk
import os
import base64
import io
import structlog
from azure.cognitiveservices.speech import ResultReason, SpeechSynthesisOutputFormat
import ffmpeg

logger = structlog.get_logger()

# Azure credentials from environment
tts_key = os.getenv("AZURE_SPEECH_KEY")
tts_region = os.getenv("AZURE_SPEECH_REGION")
def text_to_speech(text: str, target_language: str, voice_name: str = None) -> str:
    try:
        speech_config = speechsdk.SpeechConfig(subscription=tts_key, region=tts_region)

        voice_map = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "it": "it-IT-ElsaNeural",
            "pt": "pt-BR-FranciscaNeural",
            "hi": "hi-IN-SwaraNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "ru": "ru-RU-DariyaNeural",
            "ar": "ar-SA-ZariyahNeural",
            "zh": "zh-CN-XiaoxiaoNeural"
        }

        base_lang = target_language.split('-')[0]
        voice_name = voice_name or voice_map.get(base_lang, "en-US-JennyNeural")

        speech_config.speech_synthesis_voice_name = voice_name
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info("TTS synthesis completed", text_len=len(text))
            return base64.b64encode(result.audio_data).decode("utf-8")
        else:
            cancellation = result.cancellation_details
            logger.error("TTS failed", reason=cancellation.reason, details=cancellation.error_details)
            return None

    except Exception as e:
        logger.error("TTS exception", error=str(e))
        return f"[TTS ERROR: {str(e)}]"

def reencode_audio(input_path: str, output_path: str, format: str = "opus"):
    
    try:
        if format == "opus":
            (
                ffmpeg
                .input(input_path)
                .output(output_path, acodec='libopus', ar='48000', ac=2, b='128k')
                .overwrite_output()
                .run(quiet=True)
            )
        elif format == "aac":
            (
                ffmpeg
                .input(input_path)
                .output(output_path, acodec='aac', ar='48000', ac=2, b='128k')
                .overwrite_output()
                .run(quiet=True)
            )
        logger.info(f"Audio re-encoded: {input_path} -> {output_path}")
    except Exception as e:
        logger.error("Audio re-encoding failed", error=str(e))
        raise e
