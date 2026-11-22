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
    notes_url: Optional[str] = None


class TopicCreate(BaseModel):
    subject_id: int
    name: str
    notes_url: Optional[str] = None


class QuestionPart(BaseModel):
    order: int
    text: str
    is_correct: bool


class QuestionCreate(BaseModel):
    topic_id: int
    qtype: QuestionType
    stem: str
    parts: list[QuestionPart]
    explanation: Optional[str] = None
    source: QuestionSource = QuestionSource.manual
    source_external_id: Optional[str] = None


class QuestionUpdate(BaseModel):
    stem: Optional[str] = None
    parts: Optional[list[QuestionPart]] = None
    explanation: Optional[str] = None
    notes_url: Optional[str] = None


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
    given_answers: Optional[list[Optional[bool]]] = None  # one per part; true/false/null
    time_spent_seconds_delta: int = 0


class GenerateExamRequest(BaseModel):
    exam_template_id: int


class McqmedImportRequest(BaseModel):
    local_topic_id: int
    mcqmed_topic_id: str
