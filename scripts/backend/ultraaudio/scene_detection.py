
import moviepy.editor as mp
def detect_scenes(video_path, fast=True):
    # Lightweight scene detection: split every 8-12s depending on fast flag.
    clip = mp.VideoFileClip(video_path)
    dur = int(clip.duration)
    step = 12 if fast else 8
    scenes = []
    for s in range(0, dur, step):
        scenes.append({'start': float(s), 'end': float(min(dur, s+step))})
    try: clip.close()
    except: pass
    return scenes
