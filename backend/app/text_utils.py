import io, re
from pathlib import Path
from collections import Counter
from docx import Document
from pypdf import PdfReader
SUPPORTED_EXTENSIONS={".txt",".md",".docx",".pdf"}
def normalize_text(text):
    text=text.replace("\r\n","\n").replace("\r","\n")
    text=re.sub(r"[ \t]+"," ",text)
    text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()
def extract_text(filename,data):
    s=Path(filename or '').suffix.lower()
    if s not in SUPPORTED_EXTENSIONS: raise ValueError(f"Unsupported file type: {s or 'unknown'}")
    if s in {'.txt','.md'}: return normalize_text(data.decode('utf-8',errors='ignore'))
    if s=='.docx':
        d=Document(io.BytesIO(data)); return normalize_text('\n'.join(p.text for p in d.paragraphs))
    r=PdfReader(io.BytesIO(data)); return normalize_text('\n'.join((p.extract_text() or '') for p in r.pages))
def sentences(text):
    c=re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“‘])',text.strip()); return [x.strip() for x in c if len(x.strip())>=8]
def words(text): return re.findall(r"\b[\w'-]+\b",text.lower(),flags=re.UNICODE)
def ngrams(tokens,n=8): return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)] if len(tokens)>=n else []
def lexical_diversity(tokens): return len(set(tokens))/len(tokens) if tokens else 0.0
def repetition_ratio(tokens):
    if not tokens:return 0.0
    c=Counter(tokens); return sum(v for v in c.values() if v>2)/len(tokens)
