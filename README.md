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

- **Importing real questions from mcqmed.lk**: working — see
  `backend/app/importer/README.md` for the schema and how to point it at a
  new topic. Also runnable from the admin **Questions** page's "Import from
  mcqmed.lk" form. Real Cardiology content (246 questions) is already
  imported; the admin **Questions** page also supports adding questions by
  hand for subjects mcqmed doesn't have (Community Medicine, Forensic
  Medicine).

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

**Primary: this VPS, as a systemd service** (`deploy/erpm-exam.service`) —
chosen over a PaaS specifically because its free tier wipes local disk on
every deploy, which would lose the SQLite database (questions, attempts,
everything) each time. On a VPS you already control, the DB just lives on
real disk permanently.

```bash
cd frontend && npm run build                  # builds dist/, served by FastAPI
cp deploy/erpm-exam.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now erpm-exam.service
ufw allow 8020/tcp                            # or proxy it through nginx/TLS instead
```

It's currently reachable at `http://72.61.240.223:8020` — **plain HTTP, not
HTTPS**, since Let's Encrypt can't issue a certificate for a bare IP. Logins
(admin password, test-taker passcode) travel unencrypted. That's an
acceptable tradeoff for a temporary tool for one friend, but if this needs
to stick around, put it behind an nginx server block + a subdomain +
certbot (same pattern as this VPS's other sites) for real TLS.

`render.yaml` is kept as an alternative if you'd rather not self-host —
same app, but re-seed subjects/topics/templates/questions after every
deploy since Render's free tier has no persistent disk.

## Security notes

- `.env` is gitignored — never commit it. It holds the admin password hash
  and your personal mcqmed.lk session token.
- The mcqmed.lk token is yours personally — treat it like a password. Don't
  share this repo's `.env` file, and if you ever suspect it leaked, log out
  of mcqmed.lk everywhere and log back in to get a fresh one.
