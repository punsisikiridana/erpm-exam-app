from typing import Optional

from pydantic import BaseModel

from app.models.models import QuestionSource, QuestionType


class AdminLoginRequest(BaseModel):
    password: str


class TestTakerLoginRequest(BaseModel):
    name: str
    passcode: str


class SubjectCreate(BaseModel):
    name: str


class TopicCreate(BaseModel):
    subject_id: int
    name: str


class QuestionOption(BaseModel):
    label: str
    text: str


class QuestionCreate(BaseModel):
    topic_id: int
    qtype: QuestionType
    stem: str
    options: Optional[list[QuestionOption]] = None
    correct_answer: str
    explanation: Optional[str] = None
    source: QuestionSource = QuestionSource.manual
    source_external_id: Optional[str] = None


class QuestionUpdate(BaseModel):
    stem: Optional[str] = None
    options: Optional[list[QuestionOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


class ExamTemplateRuleCreate(BaseModel):
    topic_id: int
    tf_count: int = 0
    sba_count: int = 0
    order: int = 0


class ExamTemplateCreate(BaseModel):
    name: str
    time_limit_minutes: int
    rules: list[ExamTemplateRuleCreate]


class TestTakerCreate(BaseModel):
    name: str
    passcode: str


class AutosaveRequest(BaseModel):
    given_answer: Optional[str] = None
    time_spent_seconds_delta: int = 0


class GenerateExamRequest(BaseModel):
    exam_template_id: int
