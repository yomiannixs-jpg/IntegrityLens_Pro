import re,statistics,math
from collections import Counter
from .text_utils import words,sentences,lexical_diversity,repetition_ratio,paragraph_chunks
TRANSITIONS={"moreover","furthermore","additionally","consequently","therefore","however","notably","overall","in conclusion"}
FUNCTION_WORDS={"the","a","an","and","or","but","if","while","of","to","in","on","for","with","as","by","at","from","that","this","these","those","is","are","was","were","be","been","being"}
def clamp(x):return max(0,min(1,x))
def entropy(tokens):
    if not tokens:return 0
    c=Counter(tokens);n=len(tokens)
    return -sum((v/n)*math.log2(v/n) for v in c.values())
def analyze_ai_likelihood(text):
    toks=words(text);sents=sentences(text);paras=paragraph_chunks(text)
    if len(toks)<80:return {"score":0.0,"label":"Insufficient text","confidence":"low","warning":"Use at least ~80 words for a meaningful estimate.","signals":[]}
    lens=[len(words(s)) for s in sents] or [len(toks)]
    mean=statistics.mean(lens);sd=statistics.pstdev(lens) if len(lens)>1 else 0;burst=sd/max(mean,1)
    lex=lexical_diversity(toks);rep=repetition_ratio(toks);td=sum(text.lower().count(t) for t in TRANSITIONS)/max(len(sents),1);pd=len(re.findall(r"[,:;—–()]",text))/max(len(toks),1)
    ent=entropy(toks)/max(math.log2(max(len(set(toks)),2)),1);func=sum(1 for t in toks if t in FUNCTION_WORDS)/len(toks)
    plens=[len(words(p)) for p in paras] or [len(toks)];rhythm=(statistics.pstdev(plens) if len(plens)>1 else 0)/max(statistics.mean(plens),1)
    u=clamp((.42-burst)/.42);l=clamp(1-abs(lex-.48)/.30);r=clamp((.16-rep)/.16);t=clamp(td/.8);p=clamp(1-abs(pd-.065)/.065);e=clamp(1-abs(ent-.82)/.22);f=clamp(1-abs(func-.42)/.20);pr=clamp((.55-rhythm)/.55)
    raw=.23*u+.16*l+.10*r+.12*t+.08*p+.12*e+.10*f+.09*pr;sf=clamp(len(toks)/700);pct=round(clamp(.5+(raw-.5)*(.45+.55*sf))*100,1)
    label="Lower AI-like signal" if pct<35 else "Mixed / uncertain" if pct<65 else "Higher AI-like signal";conf="high" if len(toks)>=1000 else "medium" if len(toks)>=300 else "low"
    signals=[{"name":"Sentence-length uniformity","value":round(u*100,1),"explanation":"Very even sentence lengths can increase machine-like regularity."},{"name":"Lexical profile","value":round(l*100,1),"explanation":"Measures vocabulary diversity against a smooth moderate range."},{"name":"Low repetition","value":round(r*100,1),"explanation":"Repeated or idiosyncratic wording can reduce machine-like regularity."},{"name":"Transition density","value":round(t*100,1),"explanation":"Frequent formal transitions can raise the signal but are common in academic prose."},{"name":"Punctuation regularity","value":round(p*100,1),"explanation":"A regular punctuation profile can contribute to the score."},{"name":"Lexical entropy","value":round(e*100,1),"explanation":"Measures vocabulary distribution regularity."},{"name":"Function-word regularity","value":round(f*100,1),"explanation":"Function-word proportions can reveal stylistic regularity."},{"name":"Paragraph rhythm","value":round(pr*100,1),"explanation":"Very even paragraph lengths can increase machine-like regularity."}]
    return {"score":pct,"label":label,"confidence":conf,"warning":"This is a probabilistic writing-style estimate, not proof that AI was used.","signals":signals}
