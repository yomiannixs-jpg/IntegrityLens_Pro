import os,re,requests
from bs4 import BeautifulSoup
KEY=os.getenv('SERPER_API_KEY','').strip(); LIMIT=int(os.getenv('WEB_MATCH_LIMIT','5'))
def _clean(html):
    s=BeautifulSoup(html,'html.parser')
    for t in s(['script','style','noscript','svg']): t.decompose()
    return re.sub(r'\s+',' ',s.get_text(' ',strip=True))[:50000]
def search_web(query):
    if not KEY:return []
    try:
        r=requests.post('https://google.serper.dev/search',headers={'X-API-KEY':KEY,'Content-Type':'application/json'},json={'q':query,'num':LIMIT},timeout=10); r.raise_for_status(); rows=r.json().get('organic',[])
    except:return []
    out=[]
    for row in rows[:LIMIT]:
        url=row.get('link'); body=row.get('snippet',''); title=row.get('title') or url or 'Web result'
        if url:
            try:
                p=requests.get(url,timeout=8,headers={'User-Agent':'Mozilla/5.0 IntegrityLens/1.0'})
                if p.ok and 'text/html' in p.headers.get('content-type',''): body=_clean(p.text)
            except:pass
        out.append({'id':url or title,'title':title,'source':url or 'web','text':body})
    return out
