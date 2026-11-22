import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_test_taker_id
from app.models.models import ExamAttempt, ExamAttemptQuestion, ExamTemplate, ExamTemplateRule, Topic
from app.schemas import AutosaveRequest, GenerateExamRequest
from app.services.exam_generator import generate_exam
from app.services.scoring import finalize_attempt, is_past_deadline

router = APIRouter(prefix="/api/exam", tags=["exam"])


@router.get("/templates")
def list_templates_for_testtaker(test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    templates = session.exec(select(ExamTemplate)).all()
    out = []
    for t in templates:
        rules = session.exec(select(ExamTemplateRule).where(ExamTemplateRule.exam_template_id == t.id)).all()
        topic_summaries = []
        total_questions = 0
        for r in rules:
            topic = session.get(Topic, r.topic_id)
            topic_summaries.append({"topic_name": topic.name if topic else "?", "tf_count": r.tf_count, "sba_count": r.sba_count})
            total_questions += r.tf_count + r.sba_count
        out.append(
            {
                "id": t.id,
                "name": t.name,
                "time_limit_minutes": t.time_limit_minutes,
                "total_questions": total_questions,
                "topics": topic_summaries,
            }
        )
    return out


@router.get("/attempts")
def list_my_attempts(test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    attempts = session.exec(select(ExamAttempt).where(ExamAttempt.test_taker_id == test_taker_id)).all()
    templates = {t.id: t.name for t in session.exec(select(ExamTemplate)).all()}
    return [
        {
            "id": a.id,
            "template_name": templates.get(a.exam_template_id, "?"),
            "started_at": a.started_at.isoformat(),
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "score": a.score,
            "total_questions": a.total_questions,
        }
        for a in sorted(attempts, key=lambda x: x.started_at, reverse=True)
    ]


def _serialize_attempt(session: Session, attempt: ExamAttempt) -> dict:
    questions = session.exec(
        select(ExamAttemptQuestion)
        .where(ExamAttemptQuestion.exam_attempt_id == attempt.id)
        .order_by(ExamAttemptQuestion.position)
    ).all()
    return {
        "id": attempt.id,
        "started_at": attempt.started_at.isoformat(),
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "auto_submitted": attempt.auto_submitted,
        "had_repeats": attempt.had_repeats,
        "time_limit_minutes": attempt.time_limit_minutes_snapshot,
        "total_questions": attempt.total_questions,
        "score": attempt.score,
        "questions": [
            {
                "position": q.position,
                "qtype": q.qtype_snapshot,
                "stem": q.stem_snapshot,
                "options": json.loads(q.options_snapshot_json) if q.options_snapshot_json else None,
                "given_answer": q.given_answer,
                "is_correct": q.is_correct,
                "time_spent_seconds": q.time_spent_seconds,
                # correct_answer is intentionally omitted while the attempt is in progress;
                # the results endpoint includes it after submission.
            }
            for q in questions
        ],
    }


def _get_owned_attempt(session: Session, attempt_id: int, test_taker_id: int) -> ExamAttempt:
    attempt = session.get(ExamAttempt, attempt_id)
    if not attempt or attempt.test_taker_id != test_taker_id:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


def _enforce_deadline(session: Session, attempt: ExamAttempt) -> ExamAttempt:
    if attempt.submitted_at is None and is_past_deadline(attempt):
        attempt = finalize_attempt(session, attempt, auto_submitted=True)
    return attempt


@router.post("/attempts")
def start_exam(body: GenerateExamRequest, test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    attempt = generate_exam(session, test_taker_id, body.exam_template_id)
    return _serialize_attempt(session, attempt)


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: int, test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    attempt = _get_owned_attempt(session, attempt_id, test_taker_id)
    attempt = _enforce_deadline(session, attempt)
    return _serialize_attempt(session, attempt)


@router.patch("/attempts/{attempt_id}/questions/{position}")
def autosave_answer(
    attempt_id: int,
    position: int,
    body: AutosaveRequest,
    test_taker_id: int = Depends(get_current_test_taker_id),
    session: Session = Depends(get_session),
):
    attempt = _get_owned_attempt(session, attempt_id, test_taker_id)
    attempt = _enforce_deadline(session, attempt)
    if attempt.submitted_at is not None:
        raise HTTPException(status_code=400, detail="This attempt is already submitted")

    aq = session.exec(
        select(ExamAttemptQuestion).where(
            ExamAttemptQuestion.exam_attempt_id == attempt_id, ExamAttemptQuestion.position == position
        )
    ).first()
    if not aq:
        raise HTTPException(status_code=404, detail="Question not found in this attempt")

    now = datetime.utcnow()
    if aq.first_viewed_at is None:
        aq.first_viewed_at = now
    aq.last_viewed_at = now
    if body.given_answer is not None:
        aq.given_answer = body.given_answer
    aq.time_spent_seconds += max(0, body.time_spent_seconds_delta)
    session.add(aq)
    session.commit()
    return {"ok": True}


@router.post("/attempts/{attempt_id}/submit")
def submit_attempt(attempt_id: int, test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    attempt = _get_owned_attempt(session, attempt_id, test_taker_id)
    auto = is_past_deadline(attempt)
    attempt = finalize_attempt(session, attempt, auto_submitted=auto)
    return _serialize_attempt(session, attempt)


@router.get("/attempts/{attempt_id}/results")
def get_results(attempt_id: int, test_taker_id: int = Depends(get_current_test_taker_id), session: Session = Depends(get_session)):
    attempt = _get_owned_attempt(session, attempt_id, test_taker_id)
    if attempt.submitted_at is None:
        raise HTTPException(status_code=400, detail="Attempt is not submitted yet")
    questions = session.exec(
        select(ExamAttemptQuestion)
        .where(ExamAttemptQuestion.exam_attempt_id == attempt_id)
        .order_by(ExamAttemptQuestion.position)
    ).all()
    return {
        "id": attempt.id,
        "score": attempt.score,
        "total_questions": attempt.total_questions,
        "auto_submitted": attempt.auto_submitted,
        "questions": [
            {
                "position": q.position,
                "stem": q.stem_snapshot,
                "options": json.loads(q.options_snapshot_json) if q.options_snapshot_json else None,
                "given_answer": q.given_answer,
                "correct_answer": q.correct_answer_snapshot,
                "is_correct": q.is_correct,
                "time_spent_seconds": q.time_spent_seconds,
            }
            for q in questions
        ],
    }
