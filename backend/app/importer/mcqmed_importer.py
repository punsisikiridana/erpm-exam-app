"""Import questions from mcqmed.lk into the local question bank.

NOT YET FUNCTIONAL — see README.md in this directory for why, and what
you need to supply before this works. Once MCQMED_ANON_KEY is set and the
table/column names below are corrected to match reality, this becomes a
real one-way importer: read-only against mcqmed.lk, upserts locally.

Usage (once working): python -m app.importer.mcqmed_importer --topic-id 1 --mcqmed-topic-id <their-id>
"""

import argparse
import json

from sqlmodel import Session, select

from app.core.database import engine, init_db
from app.importer.mcqmed_client import McqmedClient
from app.models.models import Question, QuestionType


def _infer_qtype(row: dict) -> QuestionType:
    # PLACEHOLDER — adjust once the real schema is known. Many MCQ banks store
    # True/False questions with no options and SBA questions with an options array.
    return QuestionType.SBA if row.get("options") else QuestionType.TF


def _map_row(row: dict, local_topic_id: int) -> Question:
    # PLACEHOLDER field names — these are guesses and must be corrected against
    # the real mcqmed.lk schema before this import produces sane data.
    return Question(
        topic_id=local_topic_id,
        qtype=_infer_qtype(row),
        stem=row.get("stem") or row.get("question") or row.get("text", ""),
        options_json=json.dumps(row["options"]) if row.get("options") else None,
        correct_answer=str(row.get("correct_answer") or row.get("answer", "")),
        explanation=row.get("explanation"),
        source="mcqmed",
        source_external_id=str(row.get("id")),
    )


def import_topic(local_topic_id: int, mcqmed_topic_id: str, table: str = "questions") -> None:
    client = McqmedClient()
    rows = client.fetch_table(table, params={"select": "*", "topic_id": f"eq.{mcqmed_topic_id}"})

    inserted = updated = skipped = 0
    with Session(engine) as session:
        for row in rows:
            new_q = _map_row(row, local_topic_id)
            existing = session.exec(
                select(Question).where(Question.source == "mcqmed", Question.source_external_id == new_q.source_external_id)
            ).first()
            if existing:
                if (existing.stem, existing.options_json, existing.correct_answer, existing.explanation) != (
                    new_q.stem,
                    new_q.options_json,
                    new_q.correct_answer,
                    new_q.explanation,
                ):
                    existing.stem = new_q.stem
                    existing.options_json = new_q.options_json
                    existing.correct_answer = new_q.correct_answer
                    existing.explanation = new_q.explanation
                    session.add(existing)
                    updated += 1
                else:
                    skipped += 1
            else:
                session.add(new_q)
                inserted += 1
        session.commit()

    print(f"Done: {inserted} inserted, {updated} updated, {skipped} unchanged (out of {len(rows)} fetched).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-id", type=int, required=True, help="Local Topic.id to import into")
    parser.add_argument("--mcqmed-topic-id", type=str, required=True, help="mcqmed.lk's own topic identifier")
    parser.add_argument("--table", type=str, default="questions", help="mcqmed.lk table name (placeholder: 'questions')")
    args = parser.parse_args()

    init_db()
    import_topic(args.topic_id, args.mcqmed_topic_id, args.table)
