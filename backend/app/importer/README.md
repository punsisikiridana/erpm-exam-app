# mcqmed.lk importer — not yet functional

The importer here (`mcqmed_client.py`, `mcqmed_importer.py`) is a scaffold, not a
working integration. Two things are missing, and an automated attempt to find
them by inspecting mcqmed.lk's public JS bundle was blocked by this coding
session's safety controls as out-of-scope access to a third-party service —
so a human needs to fill them in.

## 1. The Supabase anon/public API key

mcqmed.lk's frontend talks to Supabase (project `sqhnejliuqvxiexmazlb`) via
its REST API. Every Supabase REST call needs an `apikey` header carrying the
project's public "anon" key, *in addition to* a user's personal access
token — your `MCQMED_ACCESS_TOKEN` alone isn't enough. This anon key is not
secret (it ships in every visitor's browser), so finding it is easy manually:

1. Open https://mcqmed.lk/app/ in your browser, log in, and open DevTools →
   Network tab.
2. Browse to any topic's question list.
3. Click on one of the requests going to `sqhnejliuqvxiexmazlb.supabase.co`
   and look at its request headers — copy the `apikey` header value.
4. Put it in `.env` as `MCQMED_ANON_KEY=...`.

## 2. The real table/column names and endpoint shape

While you're in that same Network tab request, also note down:

- The table name in the URL path, e.g. `/rest/v1/<table_name>?...`
- The query string — e.g. `select=...` and any `topic_id=eq.123`-style filter
  (this tells you what mcqmed calls a "topic" internally, and its id for the
  topic you were viewing).
- The response JSON's field names — question text, options, correct answer,
  explanation, etc.

Then update:
- `mcqmed_importer.py`'s `--table` default and `_map_row()`'s field-name
  guesses (`stem`, `options`, `correct_answer`, `explanation`) to match what
  you actually see.
- `mcqmed_client.fetch_table()`'s `params` usage if the filter shape differs
  from `topic_id=eq.<id>`.

## Once both are filled in

```bash
python -m app.importer.mcqmed_importer --topic-id 1 --mcqmed-topic-id <id-you-noted>
```

This is read-only against mcqmed.lk (GET requests only) and only touches the
one topic you ask for — it will never write back to mcqmed.lk or crawl its
whole question bank in one go.

## In the meantime

The admin panel's **Questions** page already supports adding/editing
questions manually in full — you don't need the importer working to start
building exam templates and having your friend practice. The importer is
purely a convenience for not retyping mcqmed.lk's existing question bank by
hand.
