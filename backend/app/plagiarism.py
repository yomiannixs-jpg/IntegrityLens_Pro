from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words, ngrams, sentences_with_spans, is_quoted_sentence, sliding_windows

MAX_DOC_SENTENCES = 450
MAX_WINDOWS_PER_SOURCE = 420
TOP_RETRIEVAL = 5

def clamp(x): return max(0.0, min(1.0, x))
def seq_ratio(a,b):
    aa,bb=" ".join(words(a))," ".join(words(b))
    return SequenceMatcher(None,aa,bb,autojunk=True).ratio() if aa and bb else 0.0
def containment(a,b,n):
    A,B=set(ngrams(words(a),n)),set(ngrams(words(b),n))
    return len(A&B)/len(A) if A else 0.0

def classify(cos,seq,g4,g5,g6):
    if g6>=.45 or seq>=.88 or (g5>=.55 and cos>=.62): return "exact_or_near_exact"
    if cos>=.58 and max(g4,g5,g6)>=.15: return "likely_paraphrase"
    if cos>=.46 or g4>=.18: return "weak_similarity"
    return "none"
def strength(cos,seq,g4,g5,g6): return clamp(.40*cos+.24*seq+.20*g4+.25*g5+.30*g6)

def _source_windows(text):
    # Fixed-size windows make a single global sparse retrieval matrix possible.
    ws=sliding_windows(text[:90000], target_words=34, step=18)
    if not ws:
        ws=[text[:5000]] if text.strip() else []
    if len(ws)>MAX_WINDOWS_PER_SOURCE:
        stride=max(1,len(ws)//MAX_WINDOWS_PER_SOURCE)
        ws=ws[::stride][:MAX_WINDOWS_PER_SOURCE]
    return ws

def compare_document(text,sources):
    meta=sentences_with_spans(text)
    total=sum(m["word_count"] for m in meta) or len(words(text))
    # Very short fragments create noise and cost; keep report rows but retrieve meaningful sentences only.
    eligible=[m for m in meta if m["word_count"]>=7][:MAX_DOC_SENTENCES]
    best={m["index"]:{"score":0,"classification":"none","source_id":None,"source_title":None,
         "source":None,"matched_text":None,"quoted":False,"discovery_score":0} for m in meta}

    windows=[]; owners=[]
    for src in sources:
        if len(words(src.get("text") or ""))<8: continue
        for w in _source_windows(src.get("text") or ""):
            if len(words(w))>=6:
                windows.append(w); owners.append(src)

    # One TF-IDF fit and one sparse matrix multiplication replaces millions of pairwise fits.
    if eligible and windows:
        docs=[m["text"] for m in eligible]
        try:
            vec=TfidfVectorizer(ngram_range=(1,2),stop_words="english",sublinear_tf=True,max_features=45000,min_df=1)
            matrix=vec.fit_transform(docs+windows)
            dmat=matrix[:len(docs)]; wmat=matrix[len(docs):]
            sims=cosine_similarity(dmat,wmat,dense_output=False).tocsr()
            for di,m in enumerate(eligible):
                row=sims.getrow(di)
                if row.nnz==0: continue
                # Only expensive-check the strongest retrieved windows.
                order=row.data.argsort()[-TOP_RETRIEVAL:][::-1]
                for pos in order:
                    wi=int(row.indices[pos]); cos=float(row.data[pos])
                    if cos<.28: continue
                    candidate=windows[wi]; src=owners[wi]
                    seq=seq_ratio(m["text"],candidate)
                    g4=containment(m["text"],candidate,4);g5=containment(m["text"],candidate,5);g6=containment(m["text"],candidate,6)
                    cls=classify(cos,seq,g4,g5,g6); sc=strength(cos,seq,g4,g5,g6)
                    if cls!="none" and sc>best[m["index"]]["score"]:
                        best[m["index"]]={"score":sc,"classification":cls,"source_id":src.get("id"),
                          "source_title":src.get("title"),"source":src.get("source"),"matched_text":candidate,
                          "quoted":is_quoted_sentence(m["text"]),"discovery_score":src.get("discovery_score",0),
                          "cosine":cos,"sequence":seq,"g4":g4,"g5":g5,"g6":g6}
        except Exception:
            pass

    matched=exact=para=quoted=0;rows=[];matches=[]
    for m in meta:
        b=best[m["index"]];wc=m["word_count"];cls=b["classification"]
        if cls in {"exact_or_near_exact","likely_paraphrase"}:
            matched+=wc
            if b["quoted"]:quoted+=wc
            elif cls=="exact_or_near_exact":exact+=wc
            else:para+=wc
            matches.append({"sentence_index":m["index"],"sentence":m["text"],"matched_text":b["matched_text"],
              "source_title":b["source_title"],"source":b["source"],"similarity":round(b["score"]*100,1),
              "classification":cls,"quoted":b["quoted"],"signals":{"tfidf":round(b.get("cosine",0)*100,1),
              "sequence":round(b.get("sequence",0)*100,1),"4gram":round(b.get("g4",0)*100,1),
              "5gram":round(b.get("g5",0)*100,1),"6gram":round(b.get("g6",0)*100,1)}})
        rows.append({**m,"classification":cls,"source_title":b["source_title"],"source":b["source"],
                     "similarity":round(b["score"]*100,1),"quoted":b["quoted"]})

    src_rows=[]
    for src in sources:
        ids=[i for i,b in best.items() if b["source_id"]==src.get("id")]
        if not ids: continue
        sw=sum(meta[i]["word_count"] for i in ids); ss=[best[i]["score"] for i in ids]
        src_rows.append({"id":src.get("id"),"title":src.get("title"),"source":src.get("source"),
          "contribution":round(100*sw/max(total,1),1),"matched_sentence_count":len(ids),
          "exact_sentence_count":sum(best[i]["classification"]=="exact_or_near_exact" for i in ids),
          "paraphrase_sentence_count":sum(best[i]["classification"]=="likely_paraphrase" for i in ids),
          "weak_sentence_count":sum(best[i]["classification"]=="weak_similarity" for i in ids),
          "average_strength":round(sum(ss)/len(ss)*100,1),"discovery_confidence":src.get("discovery_score",0),
          "fetch_kind":src.get("fetch_kind","private"),"stages":src.get("stages",[])})
    src_rows.sort(key=lambda x:(x["contribution"],x["average_strength"],x["discovery_confidence"]),reverse=True)
    matches.sort(key=lambda x:x["similarity"],reverse=True)
    mc=100*matched/max(total,1);ec=100*exact/max(total,1);pc=100*para/max(total,1);qc=100*quoted/max(total,1)
    return {"overall_similarity":round(max(0,mc-qc),1),"matched_word_coverage":round(mc,1),
      "exact_near_exact_coverage":round(ec,1),"paraphrase_coverage":round(pc,1),"quoted_coverage":round(qc,1),
      "sources":src_rows[:20],"matches":matches[:100],"document_sentences":rows,
      "engine":{"document_sentences":len(meta),"retrieval_sentences":len(eligible),"source_windows":len(windows),
                "expensive_candidates_per_sentence":TOP_RETRIEVAL}}
