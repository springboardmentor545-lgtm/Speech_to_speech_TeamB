# app/services/analytics.py
import re, math
from collections import Counter
from typing import List, Dict

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except Exception:
    NLTK_AVAILABLE = False

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except Exception:
    TEXTSTAT_AVAILABLE = False

def _tok(s: str) -> List[str]:
    s = s or ""
    s = s.lower()
    s = re.sub(r"[^\w\u00C0-\u017F]+", " ", s)
    return [t for t in s.split() if t]

def compute_bleu(reference: str, hypothesis: str) -> float:
    r = _tok(reference)
    h = _tok(hypothesis)
    if not r or not h:
        return 0.0
    if NLTK_AVAILABLE:
        smoothie = SmoothingFunction().method4
        return float(sentence_bleu([r], h, smoothing_function=smoothie) * 100.0)
    # fallback unigram precision
    rc = Counter(r)
    match = sum(min(rc[t], h.count(t)) for t in set(h))
    return float((match / max(1, len(h))) * 100.0)

def ngram_precision(reference: str, hypothesis: str, n: int) -> float:
    def grams(t, n):
        return [" ".join(t[i:i+n]) for i in range(len(t)-n+1)] if len(t) >= n else []
    r = Counter(grams(_tok(reference), n))
    h = grams(_tok(hypothesis), n)
    if not h: return 0.0
    m = 0
    for g in h:
        if r.get(g, 0) > 0:
            m += 1
            r[g] -= 1
    return float((m / len(h)) * 100.0)

def compute_ngram_precisions(reference: str, hypothesis: str) -> Dict[str, float]:
    return {f"p{i}": ngram_precision(reference, hypothesis, i) for i in (1,2,3,4)}

def _syllables(word: str) -> int:
    m = re.findall(r"[aeiouy]+", word.lower())
    return max(1, len(m))

def readability_score(text: str) -> float:
    if not text: return 0.0
    if TEXTSTAT_AVAILABLE:
        try:
            return float(textstat.flesch_reading_ease(text))
        except Exception:
            pass
    words = _tok(text)
    sents = max(1, len(re.findall(r"[.!?]+", text)))
    syll = sum(_syllables(w) for w in words)
    ASL = len(words) / sents
    ASW = syll / max(1, len(words))
    score = 206.835 - (1.015 * ASL) - (84.6 * ASW)
    return float(max(0.0, min(100.0, score)))

def quality_verdict(bleu: float, readability: float, confidence: float) -> str:
    comp = (bleu/100)*0.6 + (readability/100)*0.25 + max(0.0, min(1.0, confidence))*0.15
    if comp >= 0.8: return "Excellent"
    if comp >= 0.6: return "Good"
    if comp >= 0.4: return "Fair"
    return "Poor"

def latency_percentiles(values: List[float]) -> Dict[str, float]:
    if not values: return {"p95": 0.0, "p99": 0.0}
    arr = sorted(values)
    def pct(p):
        k = (len(arr)-1) * (p/100.0)
        f, c = math.floor(k), math.ceil(k)
        if f == c: return float(arr[int(k)])
        return float(arr[f]*(c-k) + arr[c]*(k-f))
    return {"p95": pct(95), "p99": pct(99)}