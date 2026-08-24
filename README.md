# CareerMate AI — MVP

An AI-powered career assistant: resume analysis, job search, mock interviews,
and application tracking. Covers the 5 MVP features from the original plan.

## What's included
- `backend/` — FastAPI + SQLite (swappable to Postgres), JWT auth, resume
  parsing (PDF/DOCX), rule-based ATS scoring, job search/save, application
  tracker, interview question bank with scoring.
- `frontend/` — a single `index.html` (vanilla JS, no build step) that talks
  to the backend API.

The resume analyzer and interview feedback work out of the box with **no
external API key** using rule-based logic. If you set `ANTHROPIC_API_KEY` in
`backend/.env`, both features automatically switch to Claude-generated
feedback instead — no code changes needed.

## Run it locally

**1. Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Optional: generate a real secret and paste into .env
python3 -c "import secrets; print(secrets.token_hex(32))"

python -m app.seed               # creates tables + sample jobs/questions
uvicorn app.main:app --reload --port 8000
```
Backend now runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

**2. Frontend**

No build tools needed — just serve the static file. Easiest options:
```bash
cd frontend
python3 -m http.server 5500
```
Then open `http://localhost:5500` in your browser. (Opening the HTML file
directly with `file://` also mostly works, but a local server avoids some
browser CORS quirks.)

Register a new account, and you're in.

## Extending it
- Swap `DATABASE_URL` in `.env` to a Postgres URL for production.
- Replace the sample jobs in `app/seed.py` with a real job-data source (see
  the deployment doc below for legal ways to do this).
- The `SKILL_BANK` list in `app/routers/resumes.py` is the keyword list used
  for skill detection — expand it as needed.

## Deployment & monetization
See the plan Claude gave in the chat, or the design docs you already have,
for phased deployment (Vercel + Render/Railway + managed Postgres) and
monetization strategy (freemium subscription, B2B campus licensing,
recruiter-side revenue, affiliate job boards).
