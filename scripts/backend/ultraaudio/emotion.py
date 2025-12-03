
def detect_emotion_stub(text, mode='auto'):
    if mode == 'none': return 'neutral'
    if mode.startswith('force_'): return mode.replace('force_','')
    # simple heuristic stub
    txt = text.lower()
    if any(w in txt for w in ['happy','love','great','awesome']): return 'happy'
    if any(w in txt for w in ['sad','cry','sorry','bad']): return 'sad'
    return 'neutral'
