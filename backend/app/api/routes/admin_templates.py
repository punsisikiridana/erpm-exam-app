from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_admin
from app.models.models import ExamTemplate, ExamTemplateRule
from app.schemas import ExamTemplateCreate

router = APIRouter(prefix="/api/admin", tags=["admin:templates"], dependencies=[Depends(require_admin)])


def _serialize(template: ExamTemplate, session: Session) -> dict:
    rules = session.exec(
        select(ExamTemplateRule).where(ExamTemplateRule.exam_template_id == template.id).order_by(ExamTemplateRule.order)
    ).all()
    return {
        "id": template.id,
        "name": template.name,
        "time_limit_minutes": template.time_limit_minutes,
        "is_preset": template.is_preset,
        "rules": [
            {"topic_id": r.topic_id, "tf_count": r.tf_count, "sba_count": r.sba_count, "order": r.order}
            for r in rules
        ],
    }


@router.get("/templates")
def list_templates(session: Session = Depends(get_session)):
    templates = session.exec(select(ExamTemplate)).all()
    return [_serialize(t, session) for t in templates]


@router.post("/templates")
def create_template(body: ExamTemplateCreate, session: Session = Depends(get_session)):
    if not body.rules:
        raise HTTPException(status_code=400, detail="At least one topic rule is required")
    template = ExamTemplate(name=body.name, time_limit_minutes=body.time_limit_minutes)
    session.add(template)
    session.commit()
    session.refresh(template)
    for rule in body.rules:
        session.add(
            ExamTemplateRule(
                exam_template_id=template.id,
                topic_id=rule.topic_id,
                tf_count=rule.tf_count,
                sba_count=rule.sba_count,
                order=rule.order,
            )
        )
    session.commit()
    return _serialize(template, session)


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, session: Session = Depends(get_session)):
    template = session.get(ExamTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for rule in session.exec(select(ExamTemplateRule).where(ExamTemplateRule.exam_template_id == template_id)).all():
        session.delete(rule)
    session.delete(template)
    session.commit()
    return {"ok": True}
