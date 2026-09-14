import re,statistics
from .text_utils import words,sentences,lexical_diversity,repetition_ratio
TRANS={'moreover','furthermore','additionally','consequently','therefore','however','notably','overall','in conclusion'}
def c(x,a=0,b=1): return max(a,min(b,x))
def analyze_ai_likelihood(text):
    toks=words(text); sents=sentences(text)
    if len(toks)<80:return {'score':0.0,'label':'Insufficient text','confidence':'low','warning':'Use at least ~80 words for a meaningful estimate.','signals':[]}
    lens=[len(words(s)) for s in sents] or [len(toks)]; mean=statistics.mean(lens); sd=statistics.pstdev(lens) if len(lens)>1 else 0.0; burst=sd/max(mean,1); lex=lexical_diversity(toks); rep=repetition_ratio(toks); tl=text.lower(); trans=sum(tl.count(t) for t in TRANS)/max(len(sents),1); punct=len(re.findall(r'[,:;—–()]',text))/max(len(toks),1)
    sig=[c((.42-burst)/.42),c(1-abs(lex-.48)/.30),c((.16-rep)/.16),c(trans/.8),c(1-abs(punct-.065)/.065)]
    raw=.34*sig[0]+.22*sig[1]+.16*sig[2]+.16*sig[3]+.12*sig[4]; sf=c(len(toks)/500); score=c(.5+(raw-.5)*(.45+.55*sf))*100
    label='Lower AI-like signal' if score<35 else 'Mixed / uncertain' if score<65 else 'Higher AI-like signal'; conf='high' if len(toks)>=800 else 'medium' if len(toks)>=250 else 'low'
    names=['Sentence-length uniformity','Lexical profile','Low repetition','Transition density','Punctuation regularity']; ex=['Very even sentence lengths can increase machine-like regularity.','Measures vocabulary diversity against a smooth moderate range.','Repeated/idiosyncratic wording can reduce machine-like regularity.','Frequent formal transitions can raise the signal but also occur in academic prose.','A very regular punctuation profile can contribute to the score.']
    return {'score':round(score,1),'label':label,'confidence':conf,'warning':'This is a probabilistic writing-style estimate, not proof that AI was used.','signals':[{'name':n,'value':round(v*100,1),'explanation':e} for n,v,e in zip(names,sig,ex)],'metrics':{'word_count':len(toks),'sentence_count':len(sents),'sentence_length_mean':round(mean,2),'sentence_length_stdev':round(sd,2),'burstiness':round(burst,3),'lexical_diversity':round(lex,3),'repetition_ratio':round(rep,3)}}
