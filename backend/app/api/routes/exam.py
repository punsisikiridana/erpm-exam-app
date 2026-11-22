import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_test_taker_id
from app.core.time_utils import iso_utc
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
            "started_at": iso_utc(a.started_at),
            "submitted_at": iso_utc(a.submitted_at),
            "score": a.score,
            "total_marks": a.total_marks,
            "total_questions": a.total_questions,
        }
        for a in sorted(attempts, key=lambda x: x.started_at, reverse=True)
    ]


def _given_answers(aq: ExamAttemptQuestion, n_parts: int) -> list:
    if not aq.given_answers_json:
        return [None] * n_parts
    given = json.loads(aq.given_answers_json)
    return given + [None] * (n_parts - len(given))


def _serialize_attempt(session: Session, attempt: ExamAttempt) -> dict:
    questions = session.exec(
        select(ExamAttemptQuestion)
        .where(ExamAttemptQuestion.exam_attempt_id == attempt.id)
        .order_by(ExamAttemptQuestion.position)
    ).all()
    out_questions = []
    for q in questions:
        parts = json.loads(q.parts_snapshot_json)
        out_questions.append(
            {
                "position": q.position,
                "qtype": q.qtype_snapshot,
                "stem": q.stem_snapshot,
                # correctness of each part is intentionally omitted while in progress;
                # the results endpoint includes it after submission.
                "parts": [{"order": p["order"], "text": p["text"]} for p in parts],
                "given_answers": _given_answers(q, len(parts)),
                "max_score": q.max_score,
                "time_spent_seconds": q.time_spent_seconds,
            }
        )
    return {
        "id": attempt.id,
        "started_at": iso_utc(attempt.started_at),
        "submitted_at": iso_utc(attempt.submitted_at),
        "auto_submitted": attempt.auto_submitted,
        "had_repeats": attempt.had_repeats,
        "time_limit_minutes": attempt.time_limit_minutes_snapshot,
        "total_questions": attempt.total_questions,
        "total_marks": attempt.total_marks,
        "score": attempt.score,
        "questions": out_questions,
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
    if body.given_answers is not None:
        aq.given_answers_json = json.dumps(body.given_answers)
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
    out_questions = []
    for q in questions:
        parts = json.loads(q.parts_snapshot_json)
        given = _given_answers(q, len(parts))
        out_questions.append(
            {
                "position": q.position,
                "qtype": q.qtype_snapshot,
                "stem": q.stem_snapshot,
                "parts": [
                    {"order": p["order"], "text": p["text"], "is_correct": p["is_correct"], "given": given[i]}
                    for i, p in enumerate(parts)
                ],
                "score_achieved": q.score_achieved,
                "max_score": q.max_score,
                "time_spent_seconds": q.time_spent_seconds,
            }
        )
    return {
        "id": attempt.id,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "total_questions": attempt.total_questions,
        "auto_submitted": attempt.auto_submitted,
        "questions": out_questions,
    }
