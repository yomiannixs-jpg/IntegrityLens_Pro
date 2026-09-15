# IntegrityLens Pro v2.2

v2.2 focuses on **match quality** after v2.1 established reliable web discovery.

## New in v2.2
- combines search snippet + fetched page text instead of replacing snippets
- fetches and extracts public PDF search results
- sliding-window source matching for partial sentence reuse
- 4/5/6-gram phrase overlap signals
- more flexible likely-paraphrase classification
- candidate source ranking using:
  - query hit count
  - exact-search stage
  - academic-domain hints
  - fetched page quality
- source discovery confidence separated from plagiarism evidence
- better source-level diagnostics
- all v2.1 diagnostics retained
- Python 3.12.10 pinned

## Important limitation
This is an evidence tool, not proof of misconduct.
AI-writing scores are probabilistic and should not be used alone for high-impact decisions.

## Render backend
Root Directory: backend
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT

Environment:
PYTHON_VERSION=3.12.10
FRONTEND_URL=https://your-frontend.onrender.com
SERPER_API_KEY=your_serper_key
WEB_MATCH_LIMIT=8
WEB_QUERY_COUNT=6
REQUEST_TIMEOUT=10

## Render frontend
Root Directory: frontend
Build: npm install && npm run build
Publish Directory: dist

Environment:
VITE_API_BASE_URL=https://your-backend.onrender.com
