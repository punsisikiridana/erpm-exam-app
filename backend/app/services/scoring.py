import json
from datetime import datetime

from sqlmodel import Session, select

from app.models.models import ExamAttempt, ExamAttemptQuestion, QuestionType


def _score_question(aq: ExamAttemptQuestion) -> int:
    parts = json.loads(aq.parts_snapshot_json)
    given = json.loads(aq.given_answers_json) if aq.given_answers_json else [None] * len(parts)

    if aq.qtype_snapshot == QuestionType.SBA:
        for i, part in enumerate(parts):
            if i < len(given) and given[i] is True:
                return 1 if part["is_correct"] else 0
        return 0

    # TF: each part scored independently
    score = 0
    for i, part in enumerate(parts):
        judged = given[i] if i < len(given) else None
        if judged is not None and judged == part["is_correct"]:
            score += 1
    return score


def finalize_attempt(session: Session, attempt: ExamAttempt, auto_submitted: bool) -> ExamAttempt:
    if attempt.submitted_at is not None:
        return attempt

    questions = session.exec(
        select(ExamAttemptQuestion).where(ExamAttemptQuestion.exam_attempt_id == attempt.id)
    ).all()

    total_score = 0
    for aq in questions:
        aq.score_achieved = _score_question(aq)
        total_score += aq.score_achieved
        session.add(aq)

    attempt.score = total_score
    attempt.submitted_at = datetime.utcnow()
    attempt.auto_submitted = auto_submitted
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt


def is_past_deadline(attempt: ExamAttempt) -> bool:
    deadline = attempt.started_at.timestamp() + attempt.time_limit_minutes_snapshot * 60
    return datetime.utcnow().timestamp() > deadline
