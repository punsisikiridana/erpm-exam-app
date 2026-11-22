import enum
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class QuestionType(str, enum.Enum):
    TF = "TF"
    SBA = "SBA"


class QuestionSource(str, enum.Enum):
    mcqmed = "mcqmed"
    manual = "manual"


class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)


class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", index=True)
    name: str = Field(index=True)


class Question(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("source", "source_external_id", name="uq_question_source_external_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    qtype: QuestionType
    stem: str
    options_json: Optional[str] = None  # JSON list of {label, text}; null for TF
    correct_answer: str  # "True"/"False" for TF; option label for SBA
    explanation: Optional[str] = None
    source: QuestionSource = QuestionSource.manual
    source_external_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExamTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    time_limit_minutes: int
    is_preset: bool = False


class ExamTemplateRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_template_id: int = Field(foreign_key="examtemplate.id", index=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    tf_count: int = 0
    sba_count: int = 0
    order: int = 0


class TestTaker(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    passcode_hash: str


class ExamAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_taker_id: int = Field(foreign_key="testtaker.id", index=True)
    exam_template_id: int = Field(foreign_key="examtemplate.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    auto_submitted: bool = False
    had_repeats: bool = False
    time_limit_minutes_snapshot: int = 0
    score: Optional[int] = None
    total_questions: int = 0


class ExamAttemptQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_attempt_id: int = Field(foreign_key="examattempt.id", index=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    position: int
    qtype_snapshot: QuestionType
    stem_snapshot: str
    options_snapshot_json: Optional[str] = None
    correct_answer_snapshot: str
    given_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent_seconds: int = 0
    first_viewed_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None


class SeenQuestion(SQLModel, table=True):
    test_taker_id: int = Field(foreign_key="testtaker.id", primary_key=True)
    question_id: int = Field(foreign_key="question.id", primary_key=True)
    exam_attempt_id: int = Field(foreign_key="examattempt.id")
    seen_at: datetime = Field(default_factory=datetime.utcnow)
