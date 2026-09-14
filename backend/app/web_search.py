import os, re, requests
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from .text_utils import chunk_passages, words

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()
WEB_MATCH_LIMIT = int(os.getenv("WEB_MATCH_LIMIT", "8"))
WEB_QUERY_COUNT = int(os.getenv("WEB_QUERY_COUNT", "6"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

def _canonical_url(url):
    try:
        p = urlparse(url)
        return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", "", ""))
    except Exception:
        return url

def _clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","svg","nav","footer","header","aside"]):
        tag.decompose()
    container = soup.find("article") or soup.find("main") or soup.body or soup
    return re.sub(r"\s+", " ", container.get_text(" ", strip=True))[:120000]

def _queries(text):
    passages = chunk_passages(text)
    if not passages:
        return []
    if len(passages) > WEB_QUERY_COUNT:
        idxs = [round(i*(len(passages)-1)/max(WEB_QUERY_COUNT-1,1)) for i in range(WEB_QUERY_COUNT)]
        passages = [passages[i] for i in sorted(set(idxs))]
    out = []
    for p in passages:
        toks = words(p)
        mid = max(0, len(toks)//2 - 6)
        phrase = " ".join(toks[mid:mid+12] or toks)
        if phrase:
            out.append(f'"{phrase}"')
    return out

def discover_web_sources(text):
    if not SERPER_API_KEY:
        return {"enabled": False, "queries": [], "sources": [], "message": "Live web discovery is disabled because SERPER_API_KEY is not configured."}

    found = {}
    queries = _queries(text)
    for query in queries:
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": WEB_MATCH_LIMIT},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            rows = r.json().get("organic", [])
        except Exception:
            continue

        for row in rows:
            url = row.get("link")
            if not url:
                continue
            cu = _canonical_url(url)
            if cu not in found:
                found[cu] = {
                    "id": cu,
                    "title": row.get("title") or cu,
                    "source": cu,
                    "snippet": row.get("snippet",""),
                    "query_hits": 1
                }
            else:
                found[cu]["query_hits"] += 1

    candidates = sorted(found.values(), key=lambda x: x["query_hits"], reverse=True)[:max(WEB_MATCH_LIMIT*2,12)]
    hydrated = []
    for row in candidates:
        text_body = row["snippet"]
        try:
            page = requests.get(row["source"], timeout=REQUEST_TIMEOUT, headers={"User-Agent":"Mozilla/5.0 IntegrityLensPro/2.0"})
            if page.ok and "text/html" in page.headers.get("content-type",""):
                cleaned = _clean_html(page.text)
                if len(words(cleaned)) >= 25:
                    text_body = cleaned
        except Exception:
            pass
        hydrated.append({
            "id": row["id"], "title": row["title"], "source": row["source"],
            "text": text_body, "query_hits": row["query_hits"]
        })
    return {"enabled": True, "queries": queries, "sources": hydrated, "message": f"Discovered {len(hydrated)} candidate web sources."}
