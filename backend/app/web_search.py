import io,os,re,requests
from urllib.parse import urlparse,urlunparse
from bs4 import BeautifulSoup
from pypdf import PdfReader
from .text_utils import words,sentences,distinctive_keywords

SERPER_API_KEY=os.getenv("SERPER_API_KEY","").strip()
WEB_MATCH_LIMIT=int(os.getenv("WEB_MATCH_LIMIT","8"))
WEB_QUERY_COUNT=int(os.getenv("WEB_QUERY_COUNT","6"))
REQUEST_TIMEOUT=int(os.getenv("REQUEST_TIMEOUT","10"))

ACADEMIC_HINTS=("doi.org","ssrn.com","arxiv.org",".edu","researchgate.net","springer.com","sciencedirect.com","tandfonline.com","wiley.com","oup.com","cambridge.org","jstor.org","worldbank.org","imf.org","bis.org")

def _canonical_url(url):
    try:
        p=urlparse(url)
        return urlunparse((p.scheme,p.netloc.lower(),p.path.rstrip("/"),"","",""))
    except Exception:return url

def _clean_html(html):
    soup=BeautifulSoup(html,"html.parser")
    for tag in soup(["script","style","noscript","svg","nav","footer","header","aside","form"]):tag.decompose()
    container=soup.find("article") or soup.find("main") or soup.body or soup
    return re.sub(r"\s+"," ",container.get_text(" ",strip=True))[:180000]

def _extract_pdf(data):
    reader=PdfReader(io.BytesIO(data))
    return re.sub(r"\s+"," "," ".join((p.extract_text() or "") for p in reader.pages))[:180000]

def _sample_sentences(text):
    sents=[s for s in sentences(text) if len(words(s))>=12]
    if len(sents)<=WEB_QUERY_COUNT:return sents
    idxs=[round(i*(len(sents)-1)/max(WEB_QUERY_COUNT-1,1)) for i in range(WEB_QUERY_COUNT)]
    return [sents[i] for i in sorted(set(idxs))]

def _cascade_queries(sentence):
    toks=words(sentence);out=[]
    if len(toks)>=12:
        mid=max(0,len(toks)//2-6);out.append(("exact12",f'"{" ".join(toks[mid:mid+12])}"'))
    if len(toks)>=8:
        mid=max(0,len(toks)//2-4);out.append(("exact8",f'"{" ".join(toks[mid:mid+8])}"'))
    kws=distinctive_keywords(sentence,7)
    if len(kws)>=3:out.append(("keywords"," ".join(kws)))
    return out

def _serper(query):
    r=requests.post("https://google.serper.dev/search",
        headers={"X-API-KEY":SERPER_API_KEY,"Content-Type":"application/json"},
        json={"q":query,"num":WEB_MATCH_LIMIT},timeout=REQUEST_TIMEOUT)
    if r.status_code!=200:return r.status_code,[],r.text[:500]
    return r.status_code,r.json().get("organic",[]),""

def _rank_candidate(row):
    score=row["query_hits"]*2
    if "exact12" in row["stages"]: score+=5
    elif "exact8" in row["stages"]: score+=3
    if any(h in row["source"].lower() for h in ACADEMIC_HINTS): score+=2
    return score

def discover_web_sources(text):
    d={"api_key_configured":bool(SERPER_API_KEY),"api_connected":False,"queries_attempted":0,
       "queries_successful":0,"query_failures":0,"candidate_urls":0,"pages_fetched":0,
       "pdfs_fetched":0,"pages_failed":0,"stages_used":{"exact12":0,"exact8":0,"keywords":0},
       "last_error":None}
    if not SERPER_API_KEY:
        return {"enabled":False,"sources":[],"queries":[],"diagnostics":d,"message":"SERPER_API_KEY is not configured."}
    found={};qlog=[]
    for sentence in _sample_sentences(text):
        got=False
        for stage,query in _cascade_queries(sentence):
            d["queries_attempted"]+=1;d["stages_used"][stage]+=1
            try:
                status,rows,err=_serper(query)
                qlog.append({"stage":stage,"query":query,"status":status,"results":len(rows)})
                if status==200:
                    d["api_connected"]=True;d["queries_successful"]+=1
                else:
                    d["query_failures"]+=1;d["last_error"]=f"HTTP {status}: {err}";continue
            except Exception as e:
                d["query_failures"]+=1;d["last_error"]=str(e)
                qlog.append({"stage":stage,"query":query,"status":"exception","results":0});continue
            if rows:
                got=True
                for row in rows:
                    url=row.get("link")
                    if not url:continue
                    cu=_canonical_url(url)
                    if cu not in found:
                        found[cu]={"id":cu,"title":row.get("title") or cu,"source":cu,
                                   "snippet":row.get("snippet",""),"query_hits":1,"stages":{stage}}
                    else:
                        found[cu]["query_hits"]+=1;found[cu]["stages"].add(stage)
            if got and stage in {"exact12","exact8"}:break
    d["candidate_urls"]=len(found)
    candidates=sorted(found.values(),key=_rank_candidate,reverse=True)[:max(WEB_MATCH_LIMIT*3,24)]
    hydrated=[]
    for row in candidates:
        snippet=row["snippet"] or ""
        fetched=""
        fetched_kind="snippet"
        try:
            page=requests.get(row["source"],timeout=REQUEST_TIMEOUT,
                headers={"User-Agent":"Mozilla/5.0 (compatible; IntegrityLensPro/2.2)"},allow_redirects=True)
            ctype=page.headers.get("content-type","").lower()
            if page.ok and ("application/pdf" in ctype or row["source"].lower().endswith(".pdf")):
                fetched=_extract_pdf(page.content)
                if len(words(fetched))>=25:
                    d["pdfs_fetched"]+=1;fetched_kind="pdf"
                else:
                    fetched="";d["pages_failed"]+=1
            elif page.ok and "text/html" in ctype:
                fetched=_clean_html(page.text)
                if len(words(fetched))>=25:
                    d["pages_fetched"]+=1;fetched_kind="html"
                else:
                    fetched="";d["pages_failed"]+=1
            else:
                d["pages_failed"]+=1
        except Exception:
            d["pages_failed"]+=1

        # Preserve search snippet as evidence; append fetched text rather than replace it.
        combined=(snippet+" "+fetched).strip()[:200000]
        hydrated.append({
            "id":row["id"],"title":row["title"],"source":row["source"],"text":combined,
            "snippet":snippet,"query_hits":row["query_hits"],"stages":sorted(row["stages"]),
            "fetch_kind":fetched_kind,"discovery_score":_rank_candidate(row)
        })
    return {"enabled":True,"sources":hydrated,"queries":qlog,"diagnostics":d,
            "message":f"Discovered {len(hydrated)} candidate web sources."}
