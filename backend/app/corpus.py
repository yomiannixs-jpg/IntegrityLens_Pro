from dataclasses import dataclass, asdict
from pathlib import Path
import json, uuid

STORE = Path(__file__).resolve().parent.parent / "corpus_store.json"

@dataclass
class CorpusDocument:
    id: str
    title: str
    text: str
    source: str = "private-corpus"

def _load_raw():
    if not STORE.exists():
        return []
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return []

def list_documents():
    return [CorpusDocument(**row) for row in _load_raw()]

def add_document(title, text, source="private-corpus"):
    docs = _load_raw()
    doc = CorpusDocument(str(uuid.uuid4()), title, text, source)
    docs.append(asdict(doc))
    STORE.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc
