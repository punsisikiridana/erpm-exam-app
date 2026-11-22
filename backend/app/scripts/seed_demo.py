"""Seed demo data for local verification.

Run with: python -m app.scripts.seed_demo
"""

import json
import random

from sqlmodel import Session, select

from app.core.database import engine, init_db
from app.core.security import hash_passcode
from app.models.models import Question, QuestionType, Subject, TestTaker, Topic


def make_tf(topic_id: int, i: int) -> Question:
    # 5 independent statements per stem, matching the real exam's T/F format
    parts = [
        {"order": j, "text": f"Statement {j} for T/F demo stem #{i} (topic {topic_id}).", "is_correct": bool((i + j) % 2)}
        for j in range(1, 6)
    ]
    return Question(
        topic_id=topic_id,
        qtype=QuestionType.TF,
        stem=f"Demo T/F stem #{i} for topic {topic_id}:",
        parts_json=json.dumps(parts),
        explanation=f"Demo explanation for T/F stem #{i}.",
        source="manual",
    )


def make_sba(topic_id: int, i: int) -> Question:
    correct_index = random.randrange(5)
    parts = [
        {"order": k + 1, "text": f"Option {chr(65+k)} for SBA #{i}", "is_correct": k == correct_index}
        for k in range(5)
    ]
    return Question(
        topic_id=topic_id,
        qtype=QuestionType.SBA,
        stem=f"Demo SBA question #{i} for topic {topic_id}.",
        parts_json=json.dumps(parts),
        explanation=f"Demo explanation for SBA #{i}.",
        source="manual",
    )


def main() -> None:
    init_db()
    with Session(engine) as session:
        if session.exec(select(Subject).where(Subject.name == "Medicine")).first():
            print("Demo data already present, skipping.")
            return

        subject = Subject(name="Medicine")
        session.add(subject)
        session.commit()
        session.refresh(subject)

        cardiology = Topic(subject_id=subject.id, name="Cardiology")
        respiratory = Topic(subject_id=subject.id, name="Respiratory")
        session.add(cardiology)
        session.add(respiratory)
        session.commit()
        session.refresh(cardiology)
        session.refresh(respiratory)

        for topic in (cardiology, respiratory):
            for i in range(1, 31):
                session.add(make_tf(topic.id, i))
            for i in range(1, 31):
                session.add(make_sba(topic.id, i))
        session.commit()

        taker = TestTaker(name="friend", passcode_hash=hash_passcode("letmein"))
        session.add(taker)
        session.commit()

        print(f"Seeded subject={subject.id}, cardiology={cardiology.id}, respiratory={respiratory.id}")
        print("Test-taker login: name=friend, passcode=letmein")


if __name__ == "__main__":
    main()
