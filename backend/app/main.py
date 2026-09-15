import os, io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from docx import Document
from pypdf import PdfReader
from .plagiarism import compare_document
from .web_search import discover_sources, live_validation
from .ai_detector import analyze_ai_signal

app=FastAPI(title="IntegrityLens Pro", version="2.5.0")

origins=[x.strip() for x in os.getenv("FRONTEND_URL","*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok":True,"message":"IntegrityLens Pro v2.5 API is running"}

def extract_upload(data:bytes, filename:str):
    name=(filename or "").lower()
    if name.endswith(".pdf"):
        reader=PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        doc=Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    return data.decode("utf-8",errors="ignore")

@app.post("/api/analyze")
async def analyze(
    text:str=Form(""),
    search_web:bool=Form(True),
    file:UploadFile|None=File(None)
):
    submitted=text or ""
    if file:
        submitted=extract_upload(await file.read(),file.filename)
    if not submitted.strip():
        raise HTTPException(400,"No text supplied.")
    sources=[]; diag={"api_connected":False}
    if search_web:
        sources,diag=discover_sources(submitted)
    result=compare_document(submitted,sources)
    result["ai"]=analyze_ai_signal(submitted)
    result["web"]=diag
    result["web"]["matched_sources"]=len(result["sources"])
    result["version"]="2.5.0"
    return result

@app.get("/api/self-test")
def self_test():
    src={
        "title":"IntegrityLens built-in validation source",
        "url":"internal://self-test",
        "text":(
            "IntegrityLens validation passage demonstrates deterministic exact matching across a known source. "
            "The benchmark deliberately repeats distinctive wording so the detector must attribute the overlap correctly. "
            "A successful test proves the local matching engine can recover verbatim reuse before any live web search is involved."
        )
    }
    submitted=(
        "This introductory sentence is original filler for the validation exercise. "
        +src["text"]+
        " Additional original filler follows the copied benchmark passage and should remain unmatched."
    )
    result=compare_document(submitted,[src])
    return {
        "ok": result["exact_near_exact_coverage"]>0 and len(result["sources"])>0,
        "version":"2.5.0",
        "expected":"non-zero exact match with attributed source",
        "result":result
    }

@app.get("/api/live-web-self-test")
def live_web_self_test():
    return {"version":"2.5.0", **live_validation()}
