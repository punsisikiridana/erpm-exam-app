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
    notes_url: Optional[str] = None  # fallback link to mcqmed's revision notes for this subject


class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", index=True)
    name: str = Field(index=True)
    notes_url: Optional[str] = None  # precise link to mcqmed's revision notes for this topic; overrides the subject's


class Question(SQLModel, table=True):
    """A question stem with one or more independently-correct "parts".

    For SBA: parts_json is the list of options, exactly one with is_correct=true;
    the test-taker picks one part.
    For TF: parts_json is the list of statements (typically ~5), each
    independently true or false; the test-taker judges every part, and each
    judgment is scored separately (this matches how these exams are actually
    marked — a 25-question T/F paper is 25 stems, not 25 marks).

    Each part: {"order": int, "text": str, "is_correct": bool}
    """

    __table_args__ = (UniqueConstraint("source", "source_external_id", name="uq_question_source_external_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    qtype: QuestionType
    stem: str
    parts_json: str  # JSON list of {order, text, is_correct}
    explanation: Optional[str] = None
    notes_url: Optional[str] = None  # precise link to mcqmed's revision notes for this specific question; overrides topic/subject
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
    score: Optional[int] = None  # marks achieved (sum of per-part scores)
    total_marks: int = 0  # total marks available (sum of max_score across questions)
    total_questions: int = 0  # number of question stems (not marks)


class ExamAttemptQuestion(SQLModel, table=True):
    """One served question within an attempt.

    parts_snapshot_json freezes the question's parts (text + correct answer)
    at serve time, so later edits/re-imports don't retroactively change a
    past attempt's grading.

    given_answers_json holds the test-taker's judgment per part:
    - SBA: a single-element list, e.g. ["true"] for the one option they picked
      (index into parts_snapshot matches which option), or null entries for
      parts not picked.
    - TF: one entry per part, each "true", "false", or null (unanswered).

    score_achieved / max_score let scoring work uniformly for both types:
    SBA has max_score 1, TF has max_score == number of parts.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_attempt_id: int = Field(foreign_key="examattempt.id", index=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    position: int
    qtype_snapshot: QuestionType
    stem_snapshot: str
    parts_snapshot_json: str
    given_answers_json: Optional[str] = None
    score_achieved: Optional[int] = None
    max_score: int = 1
    time_spent_seconds: int = 0
    first_viewed_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None


class SeenQuestion(SQLModel, table=True):
    test_taker_id: int = Field(foreign_key="testtaker.id", primary_key=True)
    question_id: int = Field(foreign_key="question.id", primary_key=True)
    exam_attempt_id: int = Field(foreign_key="examattempt.id")
    seen_at: datetime = Field(default_factory=datetime.utcnow)
