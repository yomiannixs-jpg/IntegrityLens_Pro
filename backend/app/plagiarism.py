from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words,ngrams,sentences,sentences_with_spans,is_quoted_sentence

def clamp(x):return max(0.0,min(1.0,x))
def seq_ratio(a,b):
    aa,bb=" ".join(words(a))," ".join(words(b))
    return SequenceMatcher(None,aa,bb).ratio() if aa and bb else 0.0
def containment(a,b,n=6):
    A,B=set(ngrams(words(a),n)),set(ngrams(words(b),n))
    return len(A&B)/len(A) if A else 0.0
def sim_matrix(qs,cs):
    try:
        v=TfidfVectorizer(ngram_range=(1,3),stop_words="english",sublinear_tf=True).fit_transform(qs+cs)
        return cosine_similarity(v[:len(qs)],v[len(qs):])
    except Exception:return None
def classify(cos,seq,ng):
    if ng>=.50 or seq>=.88:return "exact_or_near_exact"
    if cos>=.66 and max(seq,ng)>=.20:return "likely_paraphrase"
    if cos>=.48:return "weak_similarity"
    return "none"
def strength(cos,seq,ng):return clamp(.48*cos+.27*seq+.25*ng)

def compare_document(text,sources):
    meta=sentences_with_spans(text);qs=[m["text"] for m in meta]
    total=sum(m["word_count"] for m in meta) or len(words(text))
    best={i:{"score":0,"classification":"none","source_id":None,"source_title":None,"source":None,"matched_text":None,"quoted":False} for i in range(len(qs))}
    for src in sources:
        cs=sentences(src.get("text") or "")
        if not cs:continue
        sims=sim_matrix(qs,cs)
        if sims is None:continue
        for i,row in enumerate(sims):
            for j in row.argsort()[-3:][::-1]:
                cos=float(row[j])
                if cos<.42:continue
                seq=seq_ratio(qs[i],cs[int(j)]);ng=containment(qs[i],cs[int(j)],6);cls=classify(cos,seq,ng)
                if cls=="none":continue
                sc=strength(cos,seq,ng)
                if sc>best[i]["score"]:
                    best[i]={"score":sc,"classification":cls,"source_id":src.get("id"),"source_title":src.get("title"),"source":src.get("source"),"matched_text":cs[int(j)],"quoted":is_quoted_sentence(qs[i])}
    matched=exact=para=quoted=0;rows=[];matches=[]
    for i,m in enumerate(meta):
        b=best[i];wc=m["word_count"];cls=b["classification"]
        if cls in {"exact_or_near_exact","likely_paraphrase"}:
            matched+=wc
            if b["quoted"]:quoted+=wc
            elif cls=="exact_or_near_exact":exact+=wc
            else:para+=wc
            matches.append({"sentence_index":i,"sentence":m["text"],"matched_text":b["matched_text"],"source_title":b["source_title"],"source":b["source"],"similarity":round(b["score"]*100,1),"classification":cls,"quoted":b["quoted"]})
        rows.append({**m,"classification":cls,"source_title":b["source_title"],"source":b["source"],"similarity":round(b["score"]*100,1),"quoted":b["quoted"]})
    src_rows=[]
    for src in sources:
        ids=[i for i,b in best.items() if b["source_id"]==src.get("id")]
        if not ids:continue
        sw=sum(meta[i]["word_count"] for i in ids)
        src_rows.append({"id":src.get("id"),"title":src.get("title"),"source":src.get("source"),"contribution":round(100*sw/max(total,1),1),"matched_sentence_count":len(ids),"exact_sentence_count":sum(best[i]["classification"]=="exact_or_near_exact" for i in ids),"paraphrase_sentence_count":sum(best[i]["classification"]=="likely_paraphrase" for i in ids),"weak_sentence_count":sum(best[i]["classification"]=="weak_similarity" for i in ids),"average_strength":round(sum(best[i]["score"] for i in ids)/len(ids)*100,1)})
    src_rows.sort(key=lambda x:(x["contribution"],x["average_strength"]),reverse=True);matches.sort(key=lambda x:x["similarity"],reverse=True)
    mc=100*matched/max(total,1);ec=100*exact/max(total,1);pc=100*para/max(total,1);qc=100*quoted/max(total,1)
    return {"overall_similarity":round(max(0,mc-qc),1),"matched_word_coverage":round(mc,1),"exact_near_exact_coverage":round(ec,1),"paraphrase_coverage":round(pc,1),"quoted_coverage":round(qc,1),"sources":src_rows[:20],"matches":matches[:100],"document_sentences":rows}
