import io, re
from pathlib import Path
from collections import Counter
from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}

def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_text(filename, data):
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
    if suffix in {".txt", ".md"}:
        return normalize_text(data.decode("utf-8", errors="ignore"))
    if suffix == ".docx":
        doc = Document(io.BytesIO(data))
        return normalize_text("\n".join(p.text for p in doc.paragraphs))
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return normalize_text("\n".join((p.extract_text() or "") for p in reader.pages))
    return ""

def words(text):
    return re.findall(r"\b[\w'-]+\b", text.lower(), flags=re.UNICODE)

def sentences_with_spans(text):
    pattern = re.compile(r'[^.!?\n]+(?:[.!?]+|$)', re.MULTILINE)
    out = []
    for m in pattern.finditer(text):
        s = m.group(0).strip()
        wc = len(words(s))
        if wc < 4:
            continue
        out.append({"index": len(out), "text": s, "start": m.start(), "end": m.end(), "word_count": wc})
    return out

def sentences(text):
    return [x["text"] for x in sentences_with_spans(text)]

def ngrams(tokens, n=8):
    if len(tokens) < n:
        return []
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def lexical_diversity(tokens):
    return len(set(tokens))/len(tokens) if tokens else 0.0

def repetition_ratio(tokens):
    if not tokens:
        return 0.0
    c = Counter(tokens)
    return sum(v for v in c.values() if v > 2) / len(tokens)

def is_quoted_sentence(sentence, full_text):
    clean = sentence.strip()
    return (
        (clean.startswith('"') and clean.endswith('"')) or
        (clean.startswith("“") and clean.endswith("”"))
    )

def chunk_passages(text, target_words=34, overlap_words=10):
    toks = words(text)
    if not toks:
        return []
    step = max(10, target_words-overlap_words)
    out = []
    for start in range(0, len(toks), step):
        chunk = toks[start:start+target_words]
        if len(chunk) < 16:
            break
        out.append(" ".join(chunk))
    return out
