from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_admin
from app.models.models import Question, Subject, Topic
from app.schemas import SubjectCreate, TopicCreate

router = APIRouter(prefix="/api/admin", tags=["admin:subjects"], dependencies=[Depends(require_admin)])


@router.get("/subjects")
def list_subjects(session: Session = Depends(get_session)):
    subjects = session.exec(select(Subject)).all()
    result = []
    for s in subjects:
        topics = session.exec(select(Topic).where(Topic.subject_id == s.id)).all()
        result.append(
            {
                "id": s.id,
                "name": s.name,
                "notes_url": s.notes_url,
                "topics": [{"id": t.id, "name": t.name, "notes_url": t.notes_url} for t in topics],
            }
        )
    return result


@router.post("/subjects")
def create_subject(body: SubjectCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Subject).where(Subject.name == body.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Subject already exists")
    subject = Subject(name=body.name, notes_url=body.notes_url)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


@router.put("/subjects/{subject_id}")
def rename_subject(subject_id: int, body: SubjectCreate, session: Session = Depends(get_session)):
    subject = session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject.name = body.name
    subject.notes_url = body.notes_url
    session.add(subject)
    session.commit()
    return subject


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, session: Session = Depends(get_session)):
    subject = session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    topic_ids = [t.id for t in session.exec(select(Topic).where(Topic.subject_id == subject_id)).all()]
    if topic_ids:
        raise HTTPException(status_code=400, detail="Delete or move topics out of this subject first")
    session.delete(subject)
    session.commit()
    return {"ok": True}


@router.post("/topics")
def create_topic(body: TopicCreate, session: Session = Depends(get_session)):
    if not session.get(Subject, body.subject_id):
        raise HTTPException(status_code=404, detail="Subject not found")
    topic = Topic(subject_id=body.subject_id, name=body.name, notes_url=body.notes_url)
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


@router.put("/topics/{topic_id}")
def rename_topic(topic_id: int, body: TopicCreate, session: Session = Depends(get_session)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.name = body.name
    topic.subject_id = body.subject_id
    topic.notes_url = body.notes_url
    session.add(topic)
    session.commit()
    return topic


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, session: Session = Depends(get_session)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    question_count = len(session.exec(select(Question).where(Question.topic_id == topic_id)).all())
    if question_count:
        raise HTTPException(status_code=400, detail=f"Topic has {question_count} questions; delete them first")
    session.delete(topic)
    session.commit()
    return {"ok": True}
