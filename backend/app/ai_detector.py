import re, math
from collections import Counter
from .text_utils import sentences, words

def analyze_ai_signal(text):
    sents=sentences(text)
    lengths=[len(words(s)) for s in sents] or [0]
    mean=sum(lengths)/max(1,len(lengths))
    variance=sum((x-mean)**2 for x in lengths)/max(1,len(lengths))
    cv=(variance**0.5)/(mean or 1)
    ws=words(text)
    lexical=(len(set(ws))/max(1,len(ws)))*100
    # Deliberately conservative: style signal, not authorship claim.
    uniform=max(0,min(100,(1-cv)*100))
    score=round(max(0,min(100, .45*uniform + .55*(100-min(100,lexical*2)))),1)
    return {
        "score":score,
        "label":"Lower AI-like signal" if score<30 else ("Mixed / uncertain" if score<60 else "Higher AI-like signal"),
        "warning":"Probabilistic writing-style signal only. Do not use this score alone to determine authorship or misconduct.",
        "features":{"sentence_length_uniformity":round(uniform,1),"lexical_profile":round(lexical,1)}
    }
