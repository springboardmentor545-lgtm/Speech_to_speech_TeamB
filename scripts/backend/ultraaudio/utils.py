
import os, wave
def translate_stub(text, target='en'):
    # placeholder translator returns same text
    return text + ' (translated)'

def synthesize_stub(segments, azure_key, azure_region):
    # Create a silent wav as placeholder
    out = os.path.join('/tmp' if os.name!='nt' else os.environ.get('TEMP','.'), 'placeholder_tts.wav')
    import wave, struct
    framerate = 16000
    duration_s = sum([s.get('duration',1) for s in segments]) or 1
    nframes = int(framerate * duration_s)
    sine = wave.open(out,'wb')
    sine.setnchannels(1)
    sine.setsampwidth(2)
    sine.setframerate(framerate)
    silence = b'\x00\x00' * nframes
    sine.writeframes(silence)
    sine.close()
    return out
