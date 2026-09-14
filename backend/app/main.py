import os
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .text_utils import extract_text,normalize_text,words
from .corpus import list_documents,add_document
from .plagiarism import compare_against_sources
from .ai_detector import analyze_ai_likelihood
from .web_search import search_web
app=FastAPI(title='IntegrityLens Pro API',version='1.0.0')
allowed=['http://localhost:5173']
if os.getenv('FRONTEND_URL'):allowed.append(os.getenv('FRONTEND_URL'))
app.add_middleware(CORSMiddleware,allow_origins=allowed,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
class TextRequest(BaseModel): text:str; include_web:bool=False
class CorpusRequest(BaseModel): title:str; text:str
@app.get('/')
def root():return {'ok':True,'message':'IntegrityLens Pro API is running'}
@app.get('/health')
def health():return {'ok':True}
@app.get('/api/corpus')
def corpus_list():return [{'id':d.id,'title':d.title,'source':d.source,'chars':len(d.text)} for d in list_documents()]
@app.post('/api/corpus')
def corpus_add(req:CorpusRequest):
    if len(req.text.strip())<80:raise HTTPException(400,'Corpus document is too short.')
    d=add_document(req.title.strip() or 'Untitled',normalize_text(req.text)); return {'ok':True,'document':{'id':d.id,'title':d.title}}
def web_query(text):
    toks=words(text); start=max(0,len(toks)//2-7); return '"'+' '.join(toks[start:start+14])+'"' if len(toks)>=12 else text[:180]
def analyze_text(text,include_web):
    text=normalize_text(text)
    if len(words(text))<20:raise HTTPException(400,'Please provide at least 20 words.')
    private=[{'id':d.id,'title':d.title,'source':d.source,'text':d.text} for d in list_documents()]; web=search_web(web_query(text)) if include_web else []; plag=compare_against_sources(text,private+web); ai=analyze_ai_likelihood(text)
    return {'ok':True,'summary':{'word_count':len(words(text)),'plagiarism_similarity':plag['overall_similarity'],'ai_likelihood':ai['score']},'plagiarism':plag,'ai_detection':ai,'limitations':['Similarity is evidence of textual overlap, not automatically misconduct.','AI-writing scores are probabilistic and can be wrong.','Academic decisions should use source inspection and human review.']}
@app.post('/api/analyze')
def analyze(req:TextRequest):return analyze_text(req.text,req.include_web)
@app.post('/api/analyze-file')
async def analyze_file(file:UploadFile=File(...),include_web:bool=Form(False)):
    data=await file.read()
    try:text=extract_text(file.filename or 'upload.txt',data)
    except ValueError as e:raise HTTPException(400,str(e))
    return analyze_text(text,include_web)
