import os, re, requests, io
from bs4 import BeautifulSoup
from pypdf import PdfReader
from urllib.parse import urlparse
from .text_utils import distinctive_phrases, normalize, words

SERPER = "https://google.serper.dev/search"

def _timeout():
    return float(os.getenv("REQUEST_TIMEOUT","10"))

def _serper(query, num=6):
    key = os.getenv("SERPER_API_KEY","").strip()
    if not key:
        return [], "SERPER_API_KEY missing"
    try:
        r = requests.post(
            SERPER,
            headers={"X-API-KEY":key, "Content-Type":"application/json"},
            json={"q":query, "num":num},
            timeout=_timeout()
        )
        r.raise_for_status()
        data = r.json()
        return data.get("organic",[]) or [], None
    except Exception as e:
        return [], str(e)

def _clean_html(content):
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script","style","nav","footer","header","aside","form"]):
        tag.decompose()
    return normalize(soup.get_text(" "))

def _fetch(url):
    headers = {"User-Agent":"Mozilla/5.0 (compatible; IntegrityLensPro/2.5; academic-integrity-analysis)"}
    try:
        r = requests.get(url, headers=headers, timeout=_timeout(), allow_redirects=True)
        r.raise_for_status()
        ctype = (r.headers.get("content-type") or "").lower()
        if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
            reader = PdfReader(io.BytesIO(r.content))
            text = normalize(" ".join((p.extract_text() or "") for p in reader.pages[:80]))
            return text, "pdf", None
        text = _clean_html(r.text)
        return text, "html", None
    except Exception as e:
        return "", "failed", str(e)

def discover_sources(document, max_queries=None):
    max_queries = max_queries or int(os.getenv("WEB_QUERY_COUNT","24"))
    phrases = distinctive_phrases(document, phrase_words=11, max_phrases=max_queries)

    # Cascading query strategy: exact quote first, then looser phrase if exact returns nothing.
    queries, results_by_query, urls = [], [], {}
    attempts=successes=failures=0
    for phrase in phrases:
        q = f'"{phrase}"'
        attempts += 1
        organic, err = _serper(q, 6)
        mode = "exact_quote"
        if err:
            failures += 1
        else:
            successes += 1
        if not organic:
            # Remove quote restriction to improve recall.
            loose = phrase
            attempts += 1
            organic, err2 = _serper(loose, 6)
            mode = "loose_fallback"
            if err2: failures += 1
            else: successes += 1
        qrow = {"phrase":phrase, "query":q, "mode":mode, "results":[]}
        for item in organic:
            url = item.get("link")
            if not url: continue
            row = {
                "title":item.get("title",""),
                "url":url,
                "snippet":item.get("snippet","")
            }
            qrow["results"].append(row)
            if url not in urls:
                urls[url] = row
        queries.append(qrow)

    # Search snippets are evidence too. They are retained as source text even if page fetch fails.
    candidates = list(urls.values())
    fetch_cap = int(os.getenv("MAX_FETCH_URLS","32"))
    sources=[]
    html_ok=pdf_ok=fetch_failed=0
    fetch_diag=[]
    for item in candidates[:fetch_cap]:
        text, kind, err = _fetch(item["url"])
        snippet = normalize(item.get("snippet",""))
        if kind == "html": html_ok += 1
        elif kind == "pdf": pdf_ok += 1
        else: fetch_failed += 1
        combined = normalize((text + " " + snippet).strip())
        fetch_diag.append({
            "url":item["url"], "kind":kind, "error":err,
            "characters":len(combined)
        })
        if len(words(combined)) >= 8:
            sources.append({
                "title":item["title"],
                "url":item["url"],
                "text":combined,
                "kind":kind,
                "snippet_only": kind=="failed"
            })
    return sources, {
        "api_connected": bool(os.getenv("SERPER_API_KEY","").strip()),
        "queries_attempted":attempts,
        "queries_successful":successes,
        "query_failures":failures,
        "candidate_urls":len(candidates),
        "html_pages_fetched":html_ok,
        "pdfs_fetched":pdf_ok,
        "pages_failed":fetch_failed,
        "candidate_sources":len(sources),
        "queries":queries,
        "fetches":fetch_diag
    }

def live_validation():
    """Exercise the real Serper->fetch pipeline using a stable public phrase."""
    seed = (
        "We believe our research will eventually lead to artificial general intelligence, "
        "a system that can solve human-level problems."
    )
    sources, diag = discover_sources(seed, max_queries=3)
    # A successful discovery is independently useful even when a site blocks page fetch:
    needle = set(words(seed))
    hits=[]
    for s in sources:
        sw=set(words(s.get("text","")))
        overlap=len(needle & sw)/max(1,len(needle))
        if overlap >= .55:
            hits.append({"title":s["title"],"url":s["url"],"word_overlap":round(overlap*100,1)})
    return {
        "ok": bool(hits),
        "expected":"at least one public source containing the validation phrase",
        "hits":hits[:5],
        "diagnostics":diag
    }
