# ERPM Practice Exam App

A small practice-exam tool for the Sri Lankan ERPM exam. Build section-wise
practice papers (e.g. "Medicine → Cardiology only"), then progressively mix
in more topics while preferring questions the test-taker hasn't seen yet —
each paper runs under the real exam's timer (125 min / 25 T/F + 25 SBA, or
90 min / 20 T/F + 15 SBA for Psychiatry, Community Medicine, Forensic
Medicine).

## What's working

- Admin panel: manage subjects/topics, add/edit/delete questions manually,
  build exam templates (pick a time preset, mix in any number of topics with
  T/F + SBA counts each), view every attempt with per-question and
  per-topic breakdowns.
- Test-taker side: login, pick an available exam, take it with a live
  countdown + per-question pacing indicator, resume if you reload mid-exam,
  auto-submits when time runs out (enforced server-side too, so a dead tab
  can't leave an attempt open forever), review answers after submitting.
- The core "progressive mixing" logic: every exam template is just a list of
  `{topic, T/F count, SBA count}` rules — the generator automatically prefers
  questions a given test-taker hasn't seen before, and only falls back to
  repeats when a topic runs too low (flagged clearly when it happens).
- Verified end-to-end locally: backend API flow (seed → generate exam 1 →
  answer/submit → generate exam 2 confirms correct unseen/repeat mixing →
  server-side deadline enforcement) and the full UI (test-taker exam flow +
  admin panel) via an automated headless-browser run — see verification
  notes below.

## What's NOT working yet

**Importing questions from mcqmed.lk.** The importer (`backend/app/importer/`)
is a scaffold only. Supabase's REST API needs a public "anon" API key plus the
real table/column names, neither of which could be determined safely in an
automated way (this coding session's own safety controls blocked an attempt
to read it from mcqmed.lk's public JS bundle, treating it as out-of-scope
access to a third party's backend). **See
`backend/app/importer/README.md` for exactly what to do** — it's a 5-minute
manual step (open your browser's DevTools Network tab while using mcqmed.lk)
to unblock this.

In the meantime, the admin **Questions** page fully supports adding
questions by hand, so you can start building and running exams today without
the importer.

## Running it locally

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp ../.env.example ../.env
# generate an admin password hash and paste it into .env's ADMIN_PASSWORD_HASH:
.venv/bin/python -c "from app.core.security import hash_passcode; print(hash_passcode('yourpassword'))"
cp ../.env .
.venv/bin/python -m app.scripts.seed_demo   # optional: creates demo subjects/topics/questions + a "friend"/"letmein" login
.venv/bin/uvicorn app.main:app --reload --port 8010
```

```bash
cd frontend
npm install
npm run dev -- --port 5180   # dev server proxies /api to http://127.0.0.1:8010 (see vite.config.ts)
```

Then open http://127.0.0.1:5180/admin/login (admin) and
http://127.0.0.1:5180/exam/login (test-taker).

## Deploying

`render.yaml` deploys this as a single Render Web Service (FastAPI serves the
built frontend as static files, SQLite file on a persistent disk). Set the
`sync: false` env vars (`ADMIN_PASSWORD_HASH`, mcqmed credentials once you
have them) in Render's dashboard — never commit real values.

## Security notes

- `.env` is gitignored — never commit it. It holds the admin password hash
  and your personal mcqmed.lk session token.
- The mcqmed.lk token is yours personally — treat it like a password. Don't
  share this repo's `.env` file, and if you ever suspect it leaked, log out
  of mcqmed.lk everywhere and log back in to get a fresh one.
