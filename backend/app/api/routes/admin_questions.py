import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_admin
from app.models.models import Question
from app.schemas import QuestionCreate, QuestionUpdate

router = APIRouter(prefix="/api/admin", tags=["admin:questions"], dependencies=[Depends(require_admin)])


def _serialize(q: Question) -> dict:
    return {
        "id": q.id,
        "topic_id": q.topic_id,
        "qtype": q.qtype,
        "stem": q.stem,
        "parts": json.loads(q.parts_json),
        "explanation": q.explanation,
        "source": q.source,
        "source_external_id": q.source_external_id,
    }


@router.get("/questions")
def list_questions(
    topic_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Question)
    if topic_id is not None:
        stmt = stmt.where(Question.topic_id == topic_id)
    questions = session.exec(stmt).all()
    if search:
        needle = search.lower()
        questions = [q for q in questions if needle in q.stem.lower()]
    return [_serialize(q) for q in questions]


@router.post("/questions")
def create_question(body: QuestionCreate, session: Session = Depends(get_session)):
    if not body.parts:
        raise HTTPException(status_code=400, detail="At least one part is required")
    if body.qtype == "SBA" and sum(1 for p in body.parts if p.is_correct) != 1:
        raise HTTPException(status_code=400, detail="SBA questions need exactly one correct option")
    question = Question(
        topic_id=body.topic_id,
        qtype=body.qtype,
        stem=body.stem,
        parts_json=json.dumps([p.model_dump() for p in body.parts]),
        explanation=body.explanation,
        source=body.source,
        source_external_id=body.source_external_id,
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    return _serialize(question)


@router.put("/questions/{question_id}")
def update_question(question_id: int, body: QuestionUpdate, session: Session = Depends(get_session)):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if body.stem is not None:
        question.stem = body.stem
    if body.parts is not None:
        question.parts_json = json.dumps([p.model_dump() for p in body.parts])
    if body.explanation is not None:
        question.explanation = body.explanation
    session.add(question)
    session.commit()
    return _serialize(question)


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, session: Session = Depends(get_session)):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    session.delete(question)
    session.commit()
    return {"ok": True}
