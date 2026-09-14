# IntegrityLens Pro v2.1

Evidence-first plagiarism and AI-writing analysis.

## v2.1 highlights
- cascading Serper search: 12-word exact -> 8-word exact -> keyword fallback
- transparent API/search diagnostics
- actual source-page retrieval
- exact / near-exact / likely paraphrase classification
- bibliography exclusion
- quote-aware similarity accounting
- sentence-level highlighting
- matched-source attribution
- AI-writing signal panel
- printable report
- Render-ready with Python 3.12.10

## Important
Similarity is evidence of textual overlap, not proof of misconduct.
AI-writing analysis is probabilistic and should not be used alone for high-impact decisions.

## Render backend
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

Environment:
PYTHON_VERSION=3.12.10
FRONTEND_URL=https://your-frontend.onrender.com
SERPER_API_KEY=your_serper_key
WEB_MATCH_LIMIT=8
WEB_QUERY_COUNT=6
REQUEST_TIMEOUT=10

## Render frontend
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist

Environment:
VITE_API_BASE_URL=https://your-backend.onrender.com
