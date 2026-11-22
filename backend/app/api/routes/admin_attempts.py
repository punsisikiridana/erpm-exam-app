import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_admin
from app.core.time_utils import iso_utc
from app.models.models import (
    ExamAttempt,
    ExamAttemptQuestion,
    ExamTemplate,
    Question,
    Subject,
    TestTaker,
    Topic,
)

router = APIRouter(prefix="/api/admin", tags=["admin:attempts"], dependencies=[Depends(require_admin)])


@router.get("/attempts")
def list_attempts(session: Session = Depends(get_session)):
    attempts = session.exec(select(ExamAttempt)).all()
    takers = {t.id: t.name for t in session.exec(select(TestTaker)).all()}
    templates = {t.id: t.name for t in session.exec(select(ExamTemplate)).all()}
    return [
        {
            "id": a.id,
            "test_taker_name": takers.get(a.test_taker_id, "?"),
            "template_name": templates.get(a.exam_template_id, "?"),
            "started_at": iso_utc(a.started_at),
            "submitted_at": iso_utc(a.submitted_at),
            "auto_submitted": a.auto_submitted,
            "had_repeats": a.had_repeats,
            "score": a.score,
            "total_marks": a.total_marks,
            "total_questions": a.total_questions,
        }
        for a in sorted(attempts, key=lambda x: x.started_at, reverse=True)
    ]


@router.get("/attempts/{attempt_id}")
def get_attempt_detail(attempt_id: int, session: Session = Depends(get_session)):
    attempt = session.get(ExamAttempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    aqs = session.exec(
        select(ExamAttemptQuestion)
        .where(ExamAttemptQuestion.exam_attempt_id == attempt_id)
        .order_by(ExamAttemptQuestion.position)
    ).all()

    topic_cache: dict[int, Topic] = {}
    subject_notes_cache: dict[int, str | None] = {}
    per_topic = defaultdict(lambda: {"score_achieved": 0, "max_score": 0, "time_spent_seconds": 0})
    questions_out = []
    for aq in aqs:
        question = session.get(Question, aq.question_id)
        topic_id = question.topic_id if question else None
        topic = None
        if topic_id is not None:
            if topic_id not in topic_cache:
                topic_cache[topic_id] = session.get(Topic, topic_id)
            topic = topic_cache[topic_id]
        topic_name = topic.name if topic else "?"

        notes_url = question.notes_url if question and question.notes_url else None
        if not notes_url:
            notes_url = topic.notes_url if topic and topic.notes_url else None
        if not notes_url and topic:
            if topic.subject_id not in subject_notes_cache:
                subject = session.get(Subject, topic.subject_id)
                subject_notes_cache[topic.subject_id] = subject.notes_url if subject else None
            notes_url = subject_notes_cache[topic.subject_id]

        per_topic[topic_name]["max_score"] += aq.max_score
        per_topic[topic_name]["time_spent_seconds"] += aq.time_spent_seconds
        per_topic[topic_name]["score_achieved"] += aq.score_achieved or 0

        parts = json.loads(aq.parts_snapshot_json)
        given = json.loads(aq.given_answers_json) if aq.given_answers_json else [None] * len(parts)
        given = given + [None] * (len(parts) - len(given))

        questions_out.append(
            {
                "position": aq.position,
                "topic": topic_name,
                "stem": aq.stem_snapshot,
                "qtype": aq.qtype_snapshot,
                "parts": [
                    {"order": p["order"], "text": p["text"], "is_correct": p["is_correct"], "given": given[i]}
                    for i, p in enumerate(parts)
                ],
                "score_achieved": aq.score_achieved,
                "max_score": aq.max_score,
                "time_spent_seconds": aq.time_spent_seconds,
                "explanation": question.explanation if question else None,
                "notes_url": notes_url,
            }
        )

    taker = session.get(TestTaker, attempt.test_taker_id)
    template = session.get(ExamTemplate, attempt.exam_template_id)

    return {
        "id": attempt.id,
        "test_taker_name": taker.name if taker else "?",
        "template_name": template.name if template else "?",
        "started_at": iso_utc(attempt.started_at),
        "submitted_at": iso_utc(attempt.submitted_at),
        "auto_submitted": attempt.auto_submitted,
        "had_repeats": attempt.had_repeats,
        "time_limit_minutes": attempt.time_limit_minutes_snapshot,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "total_questions": attempt.total_questions,
        "per_topic_breakdown": per_topic,
        "questions": questions_out,
    }
