# IntegrityLens Pro v2

Evidence-first plagiarism and AI-writing analysis.

## v2 upgrades
- multi-passage web discovery
- actual webpage retrieval
- exact / near-exact matching
- likely paraphrase matching
- sentence-level source attribution
- document-level matched-word coverage
- quote-aware reporting
- duplicate-source consolidation
- source contribution estimates
- highlighted document review
- printable report
- existing AI-writing signal engine retained
- Render-ready
- Python pinned to 3.12.10

## Important limitation
Similarity is evidence of textual overlap, not proof of misconduct.
AI-writing analysis is probabilistic and should never be the sole basis for disciplinary, employment, legal, or academic decisions.

## Render backend
Root directory:
backend

Build:
pip install -r requirements.txt

Start:
uvicorn app.main:app --host 0.0.0.0 --port $PORT

Environment:
PYTHON_VERSION=3.12.10
FRONTEND_URL=https://your-frontend.onrender.com
SERPER_API_KEY=
WEB_MATCH_LIMIT=8
WEB_QUERY_COUNT=6
REQUEST_TIMEOUT=10

## Render frontend
Root directory:
frontend

Build:
npm install && npm run build

Publish directory:
dist

Environment:
VITE_API_BASE_URL=https://your-backend.onrender.com
