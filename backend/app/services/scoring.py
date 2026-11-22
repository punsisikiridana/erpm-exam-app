from datetime import datetime

from sqlmodel import Session, select

from app.models.models import ExamAttempt, ExamAttemptQuestion


def finalize_attempt(session: Session, attempt: ExamAttempt, auto_submitted: bool) -> ExamAttempt:
    if attempt.submitted_at is not None:
        return attempt

    questions = session.exec(
        select(ExamAttemptQuestion).where(ExamAttemptQuestion.exam_attempt_id == attempt.id)
    ).all()

    score = 0
    for q in questions:
        is_correct = (q.given_answer or "").strip().lower() == q.correct_answer_snapshot.strip().lower()
        q.is_correct = is_correct
        if is_correct:
            score += 1
        session.add(q)

    attempt.score = score
    attempt.submitted_at = datetime.utcnow()
    attempt.auto_submitted = auto_submitted
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt


def is_past_deadline(attempt: ExamAttempt) -> bool:
    deadline = attempt.started_at.timestamp() + attempt.time_limit_minutes_snapshot * 60
    return datetime.utcnow().timestamp() > deadline
