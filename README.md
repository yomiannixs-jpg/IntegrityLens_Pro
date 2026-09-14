# IntegrityLens Pro

Production-oriented plagiarism and AI-writing analysis platform.

## Features
- Paste text or upload TXT, MD, DOCX, PDF
- Private corpus plagiarism matching
- Optional live web source search via Serper
- Sentence-level overlap evidence
- Explainable AI-writing likelihood signals
- Render-ready frontend + backend

## Important limitation
AI-writing detection is probabilistic and can produce false positives/negatives. Never use the score alone for disciplinary, employment, academic, or legal action.

## Backend local run
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend local run
```bash
cd frontend
npm install
npm run dev
```

Create frontend/.env:
```env
VITE_API_BASE_URL=http://localhost:8000
```

Optional backend/.env:
```env
FRONTEND_URL=http://localhost:5173
SERPER_API_KEY=
WEB_MATCH_LIMIT=5
```

## Render
Backend Web Service: root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Frontend Static Site: root `frontend`, build `npm install && npm run build`, publish `dist`.
