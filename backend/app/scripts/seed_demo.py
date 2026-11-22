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
    answer = "True" if i % 2 == 0 else "False"
    return Question(
        topic_id=topic_id,
        qtype=QuestionType.TF,
        stem=f"Demo T/F statement #{i} for topic {topic_id}.",
        correct_answer=answer,
        explanation=f"Demo explanation for T/F #{i}.",
        source="manual",
    )


def make_sba(topic_id: int, i: int) -> Question:
    options = [{"label": c, "text": f"Option {c} for SBA #{i}"} for c in "ABCDE"]
    correct = random.choice("ABCDE")
    return Question(
        topic_id=topic_id,
        qtype=QuestionType.SBA,
        stem=f"Demo SBA question #{i} for topic {topic_id}.",
        options_json=json.dumps(options),
        correct_answer=correct,
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
