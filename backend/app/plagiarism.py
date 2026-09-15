from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words,ngrams,sentences,sentences_with_spans,is_quoted_sentence,sliding_windows

def clamp(x):return max(0.0,min(1.0,x))
def seq_ratio(a,b):
    aa,bb=" ".join(words(a))," ".join(words(b))
    return SequenceMatcher(None,aa,bb).ratio() if aa and bb else 0.0
def containment(a,b,n):
    A,B=set(ngrams(words(a),n)),set(ngrams(words(b),n))
    return len(A&B)/len(A) if A else 0.0
def tfidf_pair(a,b):
    try:
        v=TfidfVectorizer(ngram_range=(1,3),stop_words="english",sublinear_tf=True).fit_transform([a,b])
        return float(cosine_similarity(v[0:1],v[1:2])[0][0])
    except Exception:return 0.0

def classify(cos,seq,g4,g5,g6):
    # More permissive than v2.1, but still requires multiple signals.
    if g6>=.45 or seq>=.88 or (g5>=.55 and cos>=.62): return "exact_or_near_exact"
    if cos>=.58 and max(g4,g5,g6)>=.15: return "likely_paraphrase"
    if cos>=.46 or g4>=.18: return "weak_similarity"
    return "none"

def strength(cos,seq,g4,g5,g6):
    phrase=.20*g4+.25*g5+.30*g6
    return clamp(.40*cos+.24*seq+phrase)

def best_source_segment(query_sentence, source_text):
    candidates=sentences(source_text)
    # Add sliding windows so partial reuse spanning sentence boundaries can be found.
    candidates += sliding_windows(source_text, target_words=max(18,min(34,len(words(query_sentence))+6)), step=10)
    if not candidates:return None
    best=None
    for c in candidates[:1200]:
        cos=tfidf_pair(query_sentence,c)
        if cos<.30: continue
        seq=seq_ratio(query_sentence,c)
        g4=containment(query_sentence,c,4)
        g5=containment(query_sentence,c,5)
        g6=containment(query_sentence,c,6)
        cls=classify(cos,seq,g4,g5,g6)
        sc=strength(cos,seq,g4,g5,g6)
        if cls!="none" and (best is None or sc>best["score"]):
            best={"score":sc,"classification":cls,"matched_text":c,"cosine":cos,
                  "sequence":seq,"g4":g4,"g5":g5,"g6":g6}
    return best

def compare_document(text,sources):
    meta=sentences_with_spans(text);total=sum(m["word_count"] for m in meta) or len(words(text))
    best={m["index"]:{"score":0,"classification":"none","source_id":None,"source_title":None,
                      "source":None,"matched_text":None,"quoted":False,"discovery_score":0} for m in meta}

    for src in sources:
        source_text=src.get("text") or ""
        if len(words(source_text))<8: continue
        for m in meta:
            hit=best_source_segment(m["text"],source_text)
            if hit and hit["score"]>best[m["index"]]["score"]:
                best[m["index"]]={
                    "score":hit["score"],"classification":hit["classification"],
                    "source_id":src.get("id"),"source_title":src.get("title"),"source":src.get("source"),
                    "matched_text":hit["matched_text"],"quoted":is_quoted_sentence(m["text"]),
                    "discovery_score":src.get("discovery_score",0),
                    "cosine":hit["cosine"],"sequence":hit["sequence"],
                    "g4":hit["g4"],"g5":hit["g5"],"g6":hit["g6"]
                }

    matched=exact=para=quoted=0;rows=[];matches=[]
    for m in meta:
        b=best[m["index"]];wc=m["word_count"];cls=b["classification"]
        if cls in {"exact_or_near_exact","likely_paraphrase"}:
            matched+=wc
            if b["quoted"]:quoted+=wc
            elif cls=="exact_or_near_exact":exact+=wc
            else:para+=wc
            matches.append({
                "sentence_index":m["index"],"sentence":m["text"],"matched_text":b["matched_text"],
                "source_title":b["source_title"],"source":b["source"],
                "similarity":round(b["score"]*100,1),"classification":cls,"quoted":b["quoted"],
                "signals":{"tfidf":round(b.get("cosine",0)*100,1),"sequence":round(b.get("sequence",0)*100,1),
                           "4gram":round(b.get("g4",0)*100,1),"5gram":round(b.get("g5",0)*100,1),
                           "6gram":round(b.get("g6",0)*100,1)}
            })
        rows.append({**m,"classification":cls,"source_title":b["source_title"],"source":b["source"],
                     "similarity":round(b["score"]*100,1),"quoted":b["quoted"]})

    src_rows=[]
    for src in sources:
        ids=[i for i,b in best.items() if b["source_id"]==src.get("id")]
        if not ids:continue
        sw=sum(meta[i]["word_count"] for i in ids)
        source_scores=[best[i]["score"] for i in ids]
        src_rows.append({
            "id":src.get("id"),"title":src.get("title"),"source":src.get("source"),
            "contribution":round(100*sw/max(total,1),1),
            "matched_sentence_count":len(ids),
            "exact_sentence_count":sum(best[i]["classification"]=="exact_or_near_exact" for i in ids),
            "paraphrase_sentence_count":sum(best[i]["classification"]=="likely_paraphrase" for i in ids),
            "weak_sentence_count":sum(best[i]["classification"]=="weak_similarity" for i in ids),
            "average_strength":round(sum(source_scores)/len(source_scores)*100,1),
            "discovery_confidence":src.get("discovery_score",0),
            "fetch_kind":src.get("fetch_kind","private"),
            "stages":src.get("stages",[])
        })

    src_rows.sort(key=lambda x:(x["contribution"],x["average_strength"],x["discovery_confidence"]),reverse=True)
    matches.sort(key=lambda x:x["similarity"],reverse=True)
    mc=100*matched/max(total,1);ec=100*exact/max(total,1);pc=100*para/max(total,1);qc=100*quoted/max(total,1)

    return {
        "overall_similarity":round(max(0,mc-qc),1),
        "matched_word_coverage":round(mc,1),
        "exact_near_exact_coverage":round(ec,1),
        "paraphrase_coverage":round(pc,1),
        "quoted_coverage":round(qc,1),
        "sources":src_rows[:20],
        "matches":matches[:100],
        "document_sentences":rows
    }
