from collections import defaultdict
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words, ngrams, sentences, sentences_with_spans, is_quoted_sentence

def _clamp(x): return max(0.0, min(1.0, x))

def _seq(a,b):
    aa, bb = " ".join(words(a)), " ".join(words(b))
    return SequenceMatcher(None, aa, bb).ratio() if aa and bb else 0.0

def _contain(a,b,n=6):
    A, B = set(ngrams(words(a),n)), set(ngrams(words(b),n))
    return len(A&B)/len(A) if A else 0.0

def _matrix(qs, cs):
    if not qs or not cs: return None
    try:
        v = TfidfVectorizer(ngram_range=(1,3), stop_words="english", sublinear_tf=True).fit_transform(qs+cs)
        return cosine_similarity(v[:len(qs)], v[len(qs):])
    except Exception:
        return None

def _classify(cos, seq, ng):
    if ng >= .50 or seq >= .88: return "exact_or_near_exact"
    if cos >= .66 and max(seq,ng) >= .20: return "likely_paraphrase"
    if cos >= .48: return "weak_similarity"
    return "none"

def _strength(cos, seq, ng):
    return _clamp(.48*cos + .27*seq + .25*ng)

def compare_document(text, sources):
    meta = sentences_with_spans(text)
    qs = [x["text"] for x in meta]
    total_words = sum(x["word_count"] for x in meta) or len(words(text))
    best = {i:{"score":0,"classification":"none","source_id":None,"source_title":None,"source":None,"matched_text":None,"quoted":False} for i in range(len(qs))}

    for src in sources:
        cs = sentences(src.get("text") or "")
        sims = _matrix(qs, cs)
        if sims is None: continue
        for i,row in enumerate(sims):
            if len(row)==0: continue
            for j in row.argsort()[-3:][::-1]:
                cos = float(row[j])
                if cos < .42: continue
                seq = _seq(qs[i], cs[int(j)])
                ng = _contain(qs[i], cs[int(j)], 6)
                cls = _classify(cos,seq,ng)
                if cls=="none": continue
                score = _strength(cos,seq,ng)
                if score > best[i]["score"]:
                    best[i] = {
                        "score":score, "classification":cls,
                        "source_id":src.get("id"), "source_title":src.get("title"),
                        "source":src.get("source"), "matched_text":cs[int(j)],
                        "quoted":is_quoted_sentence(qs[i], text)
                    }

    matched=exact=para=quoted=0
    rows=[]; matches=[]
    for i,m in enumerate(meta):
        b=best[i]; wc=m["word_count"]; cls=b["classification"]
        if cls in {"exact_or_near_exact","likely_paraphrase"}:
            matched += wc
            if b["quoted"]: quoted += wc
            elif cls=="exact_or_near_exact": exact += wc
            else: para += wc
            matches.append({
                "sentence_index":i,"sentence":m["text"],"matched_text":b["matched_text"],
                "source_title":b["source_title"],"source":b["source"],
                "similarity":round(b["score"]*100,1),"classification":cls,"quoted":b["quoted"]
            })
        rows.append({
            **m, "classification":cls, "source_title":b["source_title"],
            "source":b["source"], "similarity":round(b["score"]*100,1), "quoted":b["quoted"]
        })

    source_rows=[]
    for src in sources:
        ids=[i for i,b in best.items() if b["source_id"]==src.get("id")]
        if not ids: continue
        src_words=sum(meta[i]["word_count"] for i in ids)
        source_rows.append({
            "id":src.get("id"),"title":src.get("title"),"source":src.get("source"),
            "contribution":round(100*src_words/max(total_words,1),1),
            "matched_sentence_count":len(ids),
            "exact_sentence_count":sum(best[i]["classification"]=="exact_or_near_exact" for i in ids),
            "paraphrase_sentence_count":sum(best[i]["classification"]=="likely_paraphrase" for i in ids),
            "weak_sentence_count":sum(best[i]["classification"]=="weak_similarity" for i in ids),
            "average_strength":round(sum(best[i]["score"] for i in ids)/len(ids)*100,1),
            "query_hits":src.get("query_hits",0)
        })
    source_rows.sort(key=lambda x:(x["contribution"],x["average_strength"]), reverse=True)
    matches.sort(key=lambda x:x["similarity"], reverse=True)

    matched_cov=100*matched/max(total_words,1)
    exact_cov=100*exact/max(total_words,1)
    para_cov=100*para/max(total_words,1)
    quote_cov=100*quoted/max(total_words,1)

    return {
        "overall_similarity":round(max(0,matched_cov-quote_cov),1),
        "matched_word_coverage":round(matched_cov,1),
        "exact_near_exact_coverage":round(exact_cov,1),
        "paraphrase_coverage":round(para_cov,1),
        "quoted_coverage":round(quote_cov,1),
        "sources":source_rows[:15],
        "matches":matches[:80],
        "document_sentences":rows
    }
