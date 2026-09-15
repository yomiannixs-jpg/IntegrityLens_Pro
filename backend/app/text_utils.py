import re
from typing import List

def normalize(text: str) -> str:
    text = (text or "").replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", normalize(text).lower())

def sentences(text: str):
    t = normalize(text)
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"'])", t)
    return [p.strip() for p in parts if len(words(p)) >= 5]

def distinctive_phrases(text: str, phrase_words=11, max_phrases=24):
    """Select long, reasonably distinctive phrases spread across the document."""
    sents = [s for s in sentences(text) if len(words(s)) >= phrase_words]
    if not sents:
        return []
    candidates = []
    for i, s in enumerate(sents):
        ws = words(s)
        # Prefer the central part of long sentences, avoiding citations/numbers-heavy starts.
        if len(ws) <= phrase_words:
            p = " ".join(ws)
        else:
            start = max(0, (len(ws) - phrase_words)//2)
            p = " ".join(ws[start:start+phrase_words])
        alpha = sum(ch.isalpha() for ch in p)
        score = alpha + len(set(ws))*2
        candidates.append((score, i, p))
    # preserve document coverage: pick from bins, then fill by score
    chosen, seen = [], set()
    step = max(1, len(candidates)//max_phrases)
    for j in range(0, len(candidates), step):
        _, _, p = max(candidates[j:j+step], default=candidates[j])
        if p not in seen:
            chosen.append(p); seen.add(p)
        if len(chosen) >= max_phrases:
            break
    if len(chosen) < max_phrases:
        for _, _, p in sorted(candidates, reverse=True):
            if p not in seen:
                chosen.append(p); seen.add(p)
            if len(chosen) >= max_phrases:
                break
    return chosen
