import sys
import os
import wave
import shutil
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock streamlit
mock_st = MagicMock()
mock_st.session_state = {
    'temp_dir': os.path.abspath('temp_test_pipeline'),
    'history': [],
    'preserve_bgm': False,
    'bgm_volume': 0.8
}
mock_st.spinner.return_value.__enter__.return_value = None
mock_st.spinner.return_value.__exit__.return_value = None
sys.modules['streamlit'] = mock_st

# Import pipeline
try:
    from scripts.backend.ultraaudio import pipeline
    from scripts.backend.ultraaudio.config import TTS_VOICE_MAP
except ImportError:
    # Try relative import if running from backend dir
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from ultraaudio import pipeline
    from ultraaudio.config import TTS_VOICE_MAP

def create_dummy_wav(path, duration_sec=3):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # Generate silence (or maybe some noise to trigger VAD if needed, but silence should be processed)
        # Actually, pure silence might be ignored by Azure Speech SDK if it thinks it's just noise.
        # Let's generate some random noise to be safe, or just silence.
        # Azure often times out on pure silence.
        import random
        noise = bytearray(random.getrandbits(8) for _ in range(16000 * duration_sec * 2))
        wf.writeframes(noise)
    print(f"Created dummy WAV at {path}")

def run_test():
    temp_dir = mock_st.session_state['temp_dir']
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    test_wav = os.path.join(temp_dir, 'test_input.wav')
    create_dummy_wav(test_wav)

    print("Starting pipeline test...")
    try:
        # Use English to Spanish
        source = 'en-US'
        target = 'es-ES' # es
        voice = TTS_VOICE_MAP['es']
        
        success = pipeline.run_pipeline(
            input_path=test_wav,
            is_video=False,
            source_code=source,
            target_code=target,
            voice_name=voice,
            chunk_sec=60,
            voice_rate='0%',
            voice_pitch='medium'
        )
        print(f"Pipeline finished. Success: {success}")
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
