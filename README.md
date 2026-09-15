# IntegrityLens Pro v2.5

v2.5 focuses on source discovery quality and auditable validation.

## New in v2.5
- exact quoted phrase searches from distinctive document passages
- cascading loose-query fallback when an exact quote returns no results
- search snippets retained as evidence even when publishers block page fetching
- HTML and PDF fetching
- query-by-query audit in the frontend
- deterministic local `/api/self-test`
- real Serper/fetch pipeline `/api/live-web-self-test`
- exact fingerprint + sparse TF-IDF shortlist matcher

## Render backend
Root directory: `backend`
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Python: 3.12.10

Required environment:
- SERPER_API_KEY
- FRONTEND_URL
Optional:
- REQUEST_TIMEOUT=10
- WEB_QUERY_COUNT=24
- MAX_FETCH_URLS=32

## Render frontend
Root directory: `frontend`
Build: `npm install && npm run build`
Publish: `dist`

Environment:
- VITE_API_BASE_URL=https://integritylens-pro.onrender.com

## Validation
1. `/api/self-test` must return `ok: true`.
2. `/api/live-web-self-test` exercises the real search/fetch pipeline and should return `ok: true`.
3. Only then use a research manuscript as a substantive test.

AI-writing scores are probabilistic style signals, not proof of AI authorship.
