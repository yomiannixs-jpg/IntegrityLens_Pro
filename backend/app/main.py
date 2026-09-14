import os
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .text_utils import extract_text,normalize_text,words,split_references
from .corpus import list_documents,add_document
from .web_search import discover_web_sources
from .plagiarism import compare_document
from .ai_detector import analyze_ai_likelihood

app=FastAPI(title="IntegrityLens Pro v2.1 API",version="2.1.0")
allowed=["http://localhost:5173"]
front=os.getenv("FRONTEND_URL","").strip()
if front:allowed.append(front.rstrip("/"))
app.add_middleware(CORSMiddleware,allow_origins=allowed,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class TextRequest(BaseModel):
    text:str
    include_web:bool=False
    exclude_references:bool=True
class CorpusRequest(BaseModel):
    title:str
    text:str

@app.get("/")
def root():return {"ok":True,"message":"IntegrityLens Pro v2.1 API is running","version":"2.1.0"}
@app.get("/health")
def health():return {"ok":True,"version":"2.1.0"}
@app.get("/api/corpus")
def corpus_list():return [{"id":d.id,"title":d.title,"source":d.source,"chars":len(d.text)} for d in list_documents()]
@app.post("/api/corpus")
def corpus_add(req:CorpusRequest):
    text=normalize_text(req.text)
    if len(words(text))<40:raise HTTPException(status_code=400,detail="Corpus document is too short.")
    d=add_document(req.title.strip() or "Untitled",text)
    return {"ok":True,"document":{"id":d.id,"title":d.title}}

def analyze_text(text,include_web,exclude_references=True):
    original=normalize_text(text)
    if len(words(original))<20:raise HTTPException(status_code=400,detail="Please provide at least 20 words.")
    body,refs,heading=split_references(original) if exclude_references else (original,"",None)
    analysis_text=body if body.strip() else original
    private=[{"id":d.id,"title":d.title,"source":d.source,"text":d.text,"query_hits":0,"stages":["private"]} for d in list_documents()]
    web={"enabled":False,"sources":[],"queries":[],"diagnostics":{"api_key_configured":False,"api_connected":False,"queries_attempted":0,"queries_successful":0,"query_failures":0,"candidate_urls":0,"pages_fetched":0,"pages_failed":0,"stages_used":{"exact12":0,"exact8":0,"keywords":0},"last_error":None},"message":"Web discovery was not requested."}
    if include_web:web=discover_web_sources(analysis_text)
    plagiarism=compare_document(analysis_text,private+web["sources"]);ai=analyze_ai_likelihood(analysis_text)
    diag=dict(web["diagnostics"]);diag["matched_sources"]=len(plagiarism["sources"])
    return {"ok":True,"version":"2.1.0","summary":{"word_count":len(words(original)),"analyzed_word_count":len(words(analysis_text)),"excluded_reference_words":len(words(refs)),"reference_heading":heading,"potential_issue_similarity":plagiarism["overall_similarity"],"matched_text_coverage":plagiarism["matched_word_coverage"],"exact_near_exact_coverage":plagiarism["exact_near_exact_coverage"],"paraphrase_coverage":plagiarism["paraphrase_coverage"],"quoted_coverage":plagiarism["quoted_coverage"],"ai_likelihood":ai["score"],"web_source_count":len(web["sources"]),"private_source_count":len(private)},"web_discovery":{"enabled":web["enabled"],"message":web["message"],"source_count":len(web["sources"]),"diagnostics":diag,"queries":web["queries"][:30]},"plagiarism":plagiarism,"ai_detection":ai,"limitations":["Similarity is evidence of textual overlap, not automatically misconduct.","Detected references can be excluded from similarity scoring, but reference detection is heuristic.","Quoted text is reported separately and excluded from the headline potential-issue score where detected.","Paraphrase matching is approximate and should be source-reviewed.","AI-writing scores are probabilistic and can be wrong.","High-impact decisions should use source inspection and human review."]}

@app.post("/api/analyze")
def analyze(req:TextRequest):return analyze_text(req.text,req.include_web,req.exclude_references)
@app.post("/api/analyze-file")
async def analyze_file(file:UploadFile=File(...),include_web:bool=Form(False),exclude_references:bool=Form(True)):
    data=await file.read()
    try:text=extract_text(file.filename or "upload.txt",data)
    except ValueError as e:raise HTTPException(status_code=400,detail=str(e))
    return analyze_text(text,include_web,exclude_references)
