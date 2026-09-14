from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words,ngrams,sentences
def phrase_overlap_score(q,c,n=8):
    a=set(ngrams(words(q),n)); b=set(ngrams(words(c),n)); return len(a & b)/len(a) if a else 0.0
def matched_sentences(q,c,threshold=.55):
    qs,cs=sentences(q),sentences(c)
    if not qs or not cs:return []
    try:v=TfidfVectorizer(ngram_range=(1,3),min_df=1).fit_transform(qs+cs)
    except:return []
    sims=cosine_similarity(v[:len(qs)],v[len(qs):]); out=[]
    for i,row in enumerate(sims):
        j=int(row.argmax()); best=float(row[j])
        if best>=threshold: out.append({'sentence':qs[i],'matched_text':cs[j],'similarity':round(best*100,1)})
    return out
def compare_against_sources(text,sources):
    kept=[s for s in sources if s.get('text')]
    if not kept:return {'overall_similarity':0.0,'sources':[],'matched_sentences':[]}
    docs=[text]+[s['text'] for s in kept]
    m=TfidfVectorizer(ngram_range=(1,3),max_features=60000,stop_words='english').fit_transform(docs); sims=cosine_similarity(m[0:1],m[1:]).flatten()
    ranked=[]; passages=[]
    for s,sim in zip(kept,sims):
        po=phrase_overlap_score(text,s['text']); hybrid=.72*float(sim)+.28*po; ms=matched_sentences(text,s['text'])
        ranked.append({'id':s.get('id'),'title':s.get('title'),'source':s.get('source'),'similarity':round(hybrid*100,1),'tfidf_similarity':round(float(sim)*100,1),'phrase_overlap':round(po*100,1),'matched_sentence_count':len(ms)})
        passages += [{**x,'source_title':s.get('title'),'source':s.get('source')} for x in ms]
    ranked.sort(key=lambda x:x['similarity'],reverse=True); passages.sort(key=lambda x:x['similarity'],reverse=True)
    return {'overall_similarity':ranked[0]['similarity'] if ranked else 0.0,'sources':ranked[:10],'matched_sentences':passages[:50]}
