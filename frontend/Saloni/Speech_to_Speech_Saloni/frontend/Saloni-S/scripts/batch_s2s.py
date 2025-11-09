# batch_s2s.py
import os, csv, time
from translate_text import translate_text
from text_to_speech import synthesize_speech

INPUT_CSV = "../samples/output/transcripts.csv"
OUTPUT_BASE = "../samples/output"

LANGUAGE_MAP = {
    "hi": "hi-IN-SwaraNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "de": "de-DE-KatjaNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "mr": "mr-IN-AarohiNeural",
    "bn": "bn-IN-TanishaaNeural",
    "gu": "gu-IN-NiranjanNeural",
    "pa": "pa-IN-AmritNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural"
}

for lang in LANGUAGE_MAP: os.makedirs(os.path.join(OUTPUT_BASE, lang), exist_ok=True)

def process():
    if not os.path.exists(INPUT_CSV):
        print("Missing CSV:", INPUT_CSV); return
    total = 0; ttot = 0
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            txt = row.get("transcript","").strip()
            if not txt: continue
            stem = os.path.splitext(row.get("filename","sample.wav"))[0]
            for lang, voice in LANGUAGE_MAP.items():
                t0=time.time()
                tr = translate_text(txt, lang)
                out = os.path.join(OUTPUT_BASE, lang, f"{stem}_{lang}.wav")
                synthesize_speech(tr, voice=voice, out_path=out)
                dt=time.time()-t0; ttot+=dt; total+=1
                print(f"{stem} → {lang} ({dt:.1f}s)")
    if total: print("Avg per audio:", round(ttot/total,2),"s")

if __name__ == "__main__":
    process()
