# mcqmed.lk importer

**Working.** The schema was captured directly from mcqmed.lk's own Network
tab (by hand, in a browser — no automated access to mcqmed's internals was
used) and confirmed against the live API.

## How it works

- `GET /rest/v1/questions?select=id,sort_order,type&is_active=eq.true&topic_id=in.(<uuid>)&order=id.asc`
  returns every active question's id + type for one topic.
- `POST /rest/v1/rpc/get_questions` with `{"p_ids": [...]}` bulk-fetches full
  content (stem, answers, explanation) for a batch of question ids.
- Both need the `apikey` header (mcqmed's public Supabase anon/publishable
  key — it ships in every visitor's browser, it's not a secret) plus the
  user's own `Authorization: Bearer <access_token>`.

mcqmed's "true_false" questions are **not** a single True/False answer —
each stem has ~5 independently-marked statements (matching how the real
exam is graded), which is why this app's `Question.parts_json` scores every
part separately rather than storing one `correct_answer`.

## What you need in `.env`

```
MCQMED_ACCESS_TOKEN=...   # your personal mcqmed.lk session token
MCQMED_REFRESH_TOKEN=...  # optional — lets the importer refresh an expired token itself
MCQMED_ANON_KEY=sb_publishable_...   # mcqmed's public Supabase key (not secret)
MCQMED_SUPABASE_URL=https://sqhnejliuqvxiexmazlb.supabase.co
```

To (re-)capture these: open https://mcqmed.lk/app/, log in, open DevTools →
Network tab, click into any topic, and find a request to
`sqhnejliuqvxiexmazlb.supabase.co`. Its request headers have `apikey` and
`authorization`. The access token expires after about an hour — if the
importer reports a refresh failure, just grab a fresh one the same way.

## Finding a topic's UUID

Click a topic in mcqmed's UI and look at the `topic_id=in.(...)` query
parameter on the resulting `/rest/v1/questions` request — that UUID is what
`--mcqmed-topic-id` / the admin panel's import form wants.

## Running it

CLI:

```bash
python -m app.importer.mcqmed_importer --topic-id 1 --mcqmed-topic-id <uuid>
```

Or from the admin panel's **Questions** page, under "Import from
mcqmed.lk" (calls the same code via `POST /api/admin/import/mcqmed`).

It's read-only against mcqmed (GET + one RPC call, never a write), scoped
to one topic at a time (never a full-bank crawl), and upserts by
`(source='mcqmed', source_external_id)` so re-running it is safe — it
only inserts new questions and updates ones whose content changed.

## Known gap

mcqmed.lk's public pages don't show Community Medicine or Forensic
Medicine as subjects. If they don't exist elsewhere on the site either,
those two subjects' questions need to go in via the admin's manual
question-entry form instead.
