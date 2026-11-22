import json
import random
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.models import (
    ExamAttempt,
    ExamAttemptQuestion,
    ExamTemplate,
    ExamTemplateRule,
    Question,
    QuestionType,
    SeenQuestion,
)


def _pick_for_rule(session: Session, test_taker_id: int, topic_id: int, qtype: QuestionType, count: int) -> list[Question]:
    if count <= 0:
        return []

    all_in_topic = session.exec(select(Question).where(Question.topic_id == topic_id, Question.qtype == qtype)).all()
    seen_ids = {
        row.question_id
        for row in session.exec(select(SeenQuestion).where(SeenQuestion.test_taker_id == test_taker_id)).all()
    }

    unseen = [q for q in all_in_topic if q.id not in seen_ids]
    seen = [q for q in all_in_topic if q.id in seen_ids]

    if len(unseen) + len(seen) < count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Topic {topic_id} only has {len(unseen) + len(seen)} {qtype.value} questions "
                f"total, need {count}. Add more questions before using this template."
            ),
        )

    random.shuffle(unseen)
    selected = unseen[:count]

    if len(selected) < count:
        shortfall = count - len(selected)
        seen.sort(key=lambda q: _last_seen_at(session, test_taker_id, q.id))
        selected += seen[:shortfall]

    return selected


def _last_seen_at(session: Session, test_taker_id: int, question_id: int) -> datetime:
    row = session.get(SeenQuestion, (test_taker_id, question_id))
    return row.seen_at if row else datetime.min


def generate_exam(session: Session, test_taker_id: int, exam_template_id: int) -> ExamAttempt:
    template = session.get(ExamTemplate, exam_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Exam template not found")

    rules = session.exec(
        select(ExamTemplateRule)
        .where(ExamTemplateRule.exam_template_id == exam_template_id)
        .order_by(ExamTemplateRule.order)
    ).all()
    if not rules:
        raise HTTPException(status_code=400, detail="This template has no topic rules configured")

    selected_before_count = 0
    all_selected: list[Question] = []
    for rule in rules:
        tf_questions = _pick_for_rule(session, test_taker_id, rule.topic_id, QuestionType.TF, rule.tf_count)
        sba_questions = _pick_for_rule(session, test_taker_id, rule.topic_id, QuestionType.SBA, rule.sba_count)
        all_selected.extend(tf_questions)
        all_selected.extend(sba_questions)
        selected_before_count += rule.tf_count + rule.sba_count

    random.shuffle(all_selected)

    seen_ids_before = {
        row.question_id
        for row in session.exec(select(SeenQuestion).where(SeenQuestion.test_taker_id == test_taker_id)).all()
    }
    had_repeats = any(q.id in seen_ids_before for q in all_selected)

    total_marks = 0
    for question in all_selected:
        parts = json.loads(question.parts_json)
        total_marks += 5 if question.qtype == QuestionType.SBA else len(parts)

    attempt = ExamAttempt(
        test_taker_id=test_taker_id,
        exam_template_id=exam_template_id,
        time_limit_minutes_snapshot=template.time_limit_minutes,
        total_questions=len(all_selected),
        total_marks=total_marks,
        had_repeats=had_repeats,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    now = datetime.utcnow()
    for position, question in enumerate(all_selected):
        parts = json.loads(question.parts_json)
        max_score = 5 if question.qtype == QuestionType.SBA else len(parts)
        session.add(
            ExamAttemptQuestion(
                exam_attempt_id=attempt.id,
                question_id=question.id,
                position=position,
                qtype_snapshot=question.qtype,
                stem_snapshot=question.stem,
                parts_snapshot_json=question.parts_json,
                max_score=max_score,
            )
        )
        if question.id not in seen_ids_before:
            session.add(SeenQuestion(test_taker_id=test_taker_id, question_id=question.id, exam_attempt_id=attempt.id, seen_at=now))

    session.commit()
    session.refresh(attempt)
    return attempt
