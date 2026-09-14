import re, statistics
from .text_utils import words, sentences, lexical_diversity, repetition_ratio

TRANSITIONS={"moreover","furthermore","additionally","consequently","therefore","however","notably","overall","in conclusion"}
def clamp(x): return max(0,min(1,x))

def analyze_ai_likelihood(text):
    toks=words(text); sents=sentences(text)
    if len(toks)<80:
        return {"score":0.0,"label":"Insufficient text","confidence":"low","warning":"Use at least ~80 words for a meaningful estimate.","signals":[]}
    lens=[len(words(s)) for s in sents] or [len(toks)]
    mean=statistics.mean(lens); sd=statistics.pstdev(lens) if len(lens)>1 else 0
    burst=sd/max(mean,1); lex=lexical_diversity(toks); rep=repetition_ratio(toks)
    td=sum(text.lower().count(t) for t in TRANSITIONS)/max(len(sents),1)
    pd=len(re.findall(r"[,:;—–()]",text))/max(len(toks),1)

    u=clamp((.42-burst)/.42)
    l=clamp(1-abs(lex-.48)/.30)
    r=clamp((.16-rep)/.16)
    t=clamp(td/.8)
    p=clamp(1-abs(pd-.065)/.065)
    raw=.34*u+.22*l+.16*r+.16*t+.12*p
    sf=clamp(len(toks)/500)
    score=clamp(.5+(raw-.5)*(.45+.55*sf))
    pct=round(score*100,1)
    label="Lower AI-like signal" if pct<35 else "Mixed / uncertain" if pct<65 else "Higher AI-like signal"
    conf="high" if len(toks)>=800 else "medium" if len(toks)>=250 else "low"
    signals=[
        {"name":"Sentence-length uniformity","value":round(u*100,1),"explanation":"Very even sentence lengths can increase machine-like regularity."},
        {"name":"Lexical profile","value":round(l*100,1),"explanation":"Measures vocabulary diversity against a smooth moderate range."},
        {"name":"Low repetition","value":round(r*100,1),"explanation":"Repeated or idiosyncratic wording can reduce machine-like regularity."},
        {"name":"Transition density","value":round(t*100,1),"explanation":"Frequent formal transitions can raise the signal but also occur in academic prose."},
        {"name":"Punctuation regularity","value":round(p*100,1),"explanation":"A regular punctuation profile can contribute to the score."}
    ]
    return {"score":pct,"label":label,"confidence":conf,"warning":"This is a probabilistic writing-style estimate, not proof that AI was used.","signals":signals}
