import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk

# Language maps
LANG_OPTIONS = {
    'English': 'en-US', 'Hindi - हिन्दी': 'hi-IN', 'French - Français': 'fr-FR', 'Spanish - Español': 'es-ES',
    'German - Deutsch': 'de-DE', 'Tamil - தமிழ்': 'ta-IN', 'Telugu - తెలుగు': 'te-IN', 'Malayalam - മലയാളം': 'ml-IN',
    'Arabic - العربية': 'ar-AE', 'Chinese - 简体中文': 'zh-CN', 'Russian - Русский': 'ru-RU',
    'Japanese - 日本語': 'ja-JP', 'Korean - 한국어': 'ko-KR', 'Italian - Italiano': 'it-IT',
    'Portuguese - Português': 'pt-BR', 'Dutch - Nederlands': 'nl-NL', 'Turkish - Türkçe': 'tr-TR',
    'Swedish - Svenska': 'sv-SE', 'Polish - Polski': 'pl-PL', 'Indonesian - Bahasa Indonesia': 'id-ID',
    'Greek - Ελληνικά': 'el-GR'
}
TRANSLATE_OPTIONS = {
    'English': 'en', 'Hindi - हिन्दी': 'hi', 'French - Français': 'fr', 'Spanish - Español': 'es',
    'German - Deutsch': 'de', 'Tamil - தமிழ்': 'ta', 'Telugu - తెలుగు': 'te', 'Malayalam - മലയാളം': 'ml',
    'Arabic - العربية': 'ar', 'Chinese - 简体中文': 'zh-cn', 'Russian - Русский': 'ru',
    'Japanese - 日本語': 'ja', 'Korean - 한국어': 'ko', 'Italian - Italiano': 'it',
    'Portuguese - Português': 'pt', 'Dutch - Nederlands': 'nl', 'Turkish - Türkçe': 'tr',
    'Swedish - Svenska': 'sv', 'Polish - Polski': 'pl', 'Indonesian - Bahasa Indonesia': 'id',
    'Greek - Ελληνικά': 'el'
}
TTS_VOICE_MAP_FEMALE = {
    'en': 'en-US-JennyNeural', 'hi': 'hi-IN-SwaraNeural', 'fr': 'fr-FR-DeniseNeural',
    'es': 'es-ES-ElviraNeural', 'de': 'de-DE-KatjaNeural', 'ta': 'ta-IN-PallaviNeural',
    'te': 'te-IN-ShrutiNeural', 'ml': 'ml-IN-SobhanaNeural', 'ar': 'ar-EG-SalmaNeural',
    'zh-cn': 'zh-CN-XiaoxiaoNeural', 'ru': 'ru-RU-SvetlanaNeural', 'ja': 'ja-JP-NanamiNeural',
    'ko': 'ko-KR-SunHiNeural', 'it': 'it-IT-ElsaNeural', 'pt': 'pt-BR-FranciscaNeural',
    'nl': 'nl-NL-ColetteNeural', 'tr': 'tr-TR-EmelNeural', 'sv': 'sv-SE-SofieNeural',
    'pl': 'pl-PL-ZofiaNeural', 'id': 'id-ID-GadisNeural', 'el': 'el-GR-AthinaNeural'
}

TTS_VOICE_MAP_MALE = {
    'en': 'en-US-GuyNeural', 'hi': 'hi-IN-MadhurNeural', 'fr': 'fr-FR-HenriNeural',
    'es': 'es-ES-AlvaroNeural', 'de': 'de-DE-ConradNeural', 'ta': 'ta-IN-ValluvarNeural',
    'te': 'te-IN-MohanNeural', 'ml': 'ml-IN-MidhunNeural', 'ar': 'ar-EG-ShakirNeural',
    'zh-cn': 'zh-CN-YunxiNeural', 'ru': 'ru-RU-DmitryNeural', 'ja': 'ja-JP-KeitaNeural',
    'ko': 'ko-KR-InJoonNeural', 'it': 'it-IT-IsaccoNeural', 'pt': 'pt-BR-AntonioNeural',
    'nl': 'nl-NL-MaartenNeural', 'tr': 'tr-TR-AhmetNeural', 'sv': 'sv-SE-MattiasNeural',
    'pl': 'pl-PL-MarekNeural', 'id': 'id-ID-ArdiNeural', 'el': 'el-GR-NestorasNeural'
}

# Default to Female for backward compatibility if needed
TTS_VOICE_MAP = TTS_VOICE_MAP_FEMALE
LANG_CODE_NAME_MAP = {code: name for name, code in TRANSLATE_OPTIONS.items()}

# Azure credentials (kept here so other modules can import)
# NOTE: This follows the original file's inline key. Consider replacing with secure config.
AZURE_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_LOCATION = "centralindia"

@st.cache_resource
def get_azure_configs():
    return AZURE_KEY, AZURE_LOCATION
