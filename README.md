# IntegrityLens Pro v2.4

Accuracy-validation build.

## New in v2.4
- deterministic 8-word fingerprint screening before fuzzy matching
- sparse TF-IDF retrieval retained for near matches/paraphrases
- increased top candidate verification from 5 to 8
- `/api/self-test` controlled benchmark endpoint
- fingerprint hit diagnostics in the matching engine
- existing Serper web search, HTML/PDF retrieval, bibliography exclusion, AI-style signals and printable report retained

## Render
Backend root: `backend`
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Frontend root: `frontend`
Build: `npm install && npm run build`
Publish: `dist`

Keep the existing backend environment variables, including `SERPER_API_KEY` and `FRONTEND_URL`.

## Validation
After deployment open backend `/api/self-test`. `ok` must be `true` and exact match coverage must be non-zero. Then test a known verbatim public passage with live web enabled before interpreting zero-similarity results on unknown documents.
