import hashlib
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .text_utils import words, sentences, normalize

def _fingerprints(text, n=8):
    ws = words(text)
    grams = [tuple(ws[i:i+n]) for i in range(max(0, len(ws)-n+1))]
    return {
        hashlib.blake2b(" ".join(g).encode("utf-8"), digest_size=8).digest()
        for g in grams
    }

def _windows(text, size=42, stride=20):
    ws = words(text)
    if len(ws) <= size:
        return [" ".join(ws)] if ws else []
    out = []
    for i in range(0, len(ws)-size+1, stride):
        out.append(" ".join(ws[i:i+size]))
    if out and out[-1] != " ".join(ws[-size:]):
        out.append(" ".join(ws[-size:]))
    return out

def compare_document(submitted, sources):
    doc_sents = sentences(submitted)
    eligible = [{"index":i, "text":s, "wc":len(words(s))} for i,s in enumerate(doc_sents) if len(words(s)) >= 7]
    doc_fp = {m["index"]:_fingerprints(m["text"]) for m in eligible}

    source_windows, window_meta = [], []
    for src in sources:
        for w in _windows(src.get("text","")):
            source_windows.append(w)
            window_meta.append(src)

    vectorizer = None
    matrix = None
    if source_windows and eligible:
        corpus = source_windows + [m["text"] for m in eligible]
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1, max_features=60000)
            matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            vectorizer = matrix = None

    matches = []
    covered = exact_words = para_words = quoted_words = 0
    source_stats = {}

    for k,m in enumerate(eligible):
        best = None
        mfp = doc_fp[m["index"]]
        candidate_ids = list(range(len(source_windows)))

        if matrix is not None and source_windows:
            qrow = matrix[len(source_windows)+k]
            sims = cosine_similarity(qrow, matrix[:len(source_windows)]).ravel()
            candidate_ids = sims.argsort()[-8:][::-1].tolist()

        for wid in candidate_ids:
            sw = source_windows[wid]
            src = window_meta[wid]
            sfp = _fingerprints(sw)
            fp_overlap = (len(mfp & sfp) / max(1, len(mfp))) if mfp else 0
            seq = SequenceMatcher(None, normalize(m["text"]).lower(), normalize(sw).lower()).ratio()
            tfidf = 0
            if matrix is not None:
                tfidf = float(cosine_similarity(
                    matrix[len(source_windows)+k], matrix[wid]
                )[0,0])
            score = max(fp_overlap, seq, tfidf)
            cls = "none"
            if fp_overlap >= .35 or seq >= .86 or tfidf >= .82:
                cls = "exact_or_near_exact"
            elif tfidf >= .48 or seq >= .62:
                cls = "likely_paraphrase"
            if cls != "none" and (best is None or score > best["similarity"]/100):
                best = {
                    "sentence_index": m["index"],
                    "sentence": m["text"],
                    "source_title": src.get("title") or src.get("url") or "Source",
                    "source": src.get("url"),
                    "similarity": round(score*100,1),
                    "classification": cls,
                    "quoted": False,
                    "signals": {
                        "tfidf": round(tfidf*100,1),
                        "sequence": round(seq*100,1),
                        "fingerprint": round(fp_overlap*100,1)
                    }
                }
        if best:
            matches.append(best)
            covered += m["wc"]
            if best["classification"] == "exact_or_near_exact":
                exact_words += m["wc"]
            else:
                para_words += m["wc"]
            key = best["source"] or best["source_title"]
            st = source_stats.setdefault(key, {
                "title":best["source_title"], "url":best["source"],
                "matched_words":0, "sentences":0, "best_similarity":0
            })
            st["matched_words"] += m["wc"]
            st["sentences"] += 1
            st["best_similarity"] = max(st["best_similarity"], best["similarity"])

    total = max(1, sum(len(words(s)) for s in doc_sents))
    sources_out = sorted(source_stats.values(), key=lambda x:(x["matched_words"],x["best_similarity"]), reverse=True)
    return {
        "overall_similarity": round(100*covered/total,1),
        "matched_word_coverage": round(100*covered/total,1),
        "exact_near_exact_coverage": round(100*exact_words/total,1),
        "paraphrase_coverage": round(100*para_words/total,1),
        "quoted_coverage": round(100*quoted_words/total,1),
        "sources": sources_out,
        "matches": matches,
        "engine": {
            "document_sentences":len(doc_sents),
            "retrieval_windows":len(source_windows),
            "fingerprint_ngram":8,
            "shortlist_per_sentence":8
        }
    }
