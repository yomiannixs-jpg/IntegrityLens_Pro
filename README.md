# IntegrityLens Pro v2.3

Performance-focused upgrade for long academic documents on modest Render instances.

## v2.3 matching architecture
- Fits one sparse TF-IDF index across document sentences and bounded source windows.
- Uses one sparse matrix retrieval operation rather than fitting TF-IDF for every sentence/window pair.
- Runs SequenceMatcher and 4/5/6-gram verification only on the top 5 retrieved passages per document sentence.
- Caps document retrieval sentences at 450 and source windows at 420 per source.
- Keeps v2.2 web discovery, snippets, public-PDF extraction, quotation handling, diagnostics, and AI-likelihood reporting.
- A zero similarity result remains valid when retrieved evidence does not support overlap.

## Render
Backend root: `backend`
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Frontend root: `frontend`
Build: `npm install && npm run build`
Publish: `dist`

Keep existing backend environment variables, including `SERPER_API_KEY`, `FRONTEND_URL`, and Python 3.12.
