"""Import questions from mcqmed.lk into the local question bank.

One-way, read-only against mcqmed.lk: fetches a single topic's questions
(never a full-bank crawl) and upserts them locally by (source='mcqmed',
source_external_id=<mcqmed question uuid>) — never writes back to mcqmed.

Usage: python -m app.importer.mcqmed_importer --topic-id 1 --mcqmed-topic-id <uuid>
"""

import argparse
import json

from sqlmodel import Session, select

from app.core.database import engine, init_db
from app.importer.mcqmed_client import McqmedClient
from app.models.models import Question, QuestionType

_TYPE_MAP = {"sba": QuestionType.SBA, "true_false": QuestionType.TF}


def _map_row(row: dict, local_topic_id: int) -> Question:
    answers = sorted(row.get("answers", []), key=lambda a: a.get("sort_order", 0))
    parts = [{"order": a.get("sort_order", i + 1), "text": a["body"], "is_correct": bool(a["is_correct"])} for i, a in enumerate(answers)]
    return Question(
        topic_id=local_topic_id,
        qtype=_TYPE_MAP[row["type"]],
        stem=row["stem"],
        parts_json=json.dumps(parts),
        explanation=row.get("explanation"),
        source="mcqmed",
        source_external_id=str(row["id"]),
    )


def import_topic(local_topic_id: int, mcqmed_topic_id: str) -> None:
    client = McqmedClient()

    id_rows = client.list_topic_question_ids(mcqmed_topic_id)
    print(f"Found {len(id_rows)} active questions in mcqmed topic {mcqmed_topic_id}.")
    if not id_rows:
        return

    full_rows = client.get_questions([r["id"] for r in id_rows])
    print(f"Fetched full content for {len(full_rows)} questions.")

    inserted = updated = skipped = 0
    with Session(engine) as session:
        for row in full_rows:
            if row.get("type") not in _TYPE_MAP:
                print(f"Skipping question {row.get('id')} with unrecognized type {row.get('type')!r}")
                continue
            new_q = _map_row(row, local_topic_id)
            existing = session.exec(
                select(Question).where(Question.source == "mcqmed", Question.source_external_id == new_q.source_external_id)
            ).first()
            if existing:
                if (existing.stem, existing.parts_json, existing.explanation) != (new_q.stem, new_q.parts_json, new_q.explanation):
                    existing.stem = new_q.stem
                    existing.parts_json = new_q.parts_json
                    existing.explanation = new_q.explanation
                    session.add(existing)
                    updated += 1
                else:
                    skipped += 1
            else:
                session.add(new_q)
                inserted += 1
        session.commit()

    print(f"Done: {inserted} inserted, {updated} updated, {skipped} unchanged (out of {len(full_rows)} fetched).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-id", type=int, required=True, help="Local Topic.id to import into")
    parser.add_argument("--mcqmed-topic-id", type=str, required=True, help="mcqmed.lk's topic UUID")
    args = parser.parse_args()

    init_db()
    import_topic(args.topic_id, args.mcqmed_topic_id)
