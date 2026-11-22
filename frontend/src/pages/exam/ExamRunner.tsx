import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Countdown } from "../../components/Countdown";
import { PacingIndicator } from "../../components/PacingIndicator";
import { QuestionCard } from "../../components/QuestionCard";
import { api, ApiError, type Attempt } from "../../lib/api";

export function ExamRunner() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [current, setCurrent] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const viewStartedAtRef = useRef<number>(Date.now());
  const submittedRef = useRef(false);

  useEffect(() => {
    api
      .get<Attempt>(`/exam/attempts/${attemptId}`)
      .then((data) => {
        if (data.submitted_at) {
          navigate(`/exam/attempts/${attemptId}/results`, { replace: true });
          return;
        }
        setAttempt(data);
        viewStartedAtRef.current = Date.now();
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/exam/login");
        else setError("Could not load this exam attempt");
      });
  }, [attemptId, navigate]);

  const flushTime = useCallback(
    async (position: number, givenAnswers?: (boolean | null)[]) => {
      const elapsed = Math.round((Date.now() - viewStartedAtRef.current) / 1000);
      viewStartedAtRef.current = Date.now();
      try {
        await api.patch(`/exam/attempts/${attemptId}/questions/${position}`, {
          given_answers: givenAnswers,
          time_spent_seconds_delta: elapsed,
        });
      } catch {
        // best-effort autosave; ignore transient failures
      }
    },
    [attemptId]
  );

  const goTo = useCallback(
    (nextIndex: number) => {
      if (!attempt) return;
      flushTime(current);
      setCurrent(Math.max(0, Math.min(nextIndex, attempt.questions.length - 1)));
    },
    [attempt, current, flushTime]
  );

  function handleAnswer(givenAnswers: (boolean | null)[]) {
    if (!attempt) return;
    setAttempt({
      ...attempt,
      questions: attempt.questions.map((q) => (q.position === current ? { ...q, given_answers: givenAnswers } : q)),
    });
    flushTime(current, givenAnswers);
  }

  const doSubmit = useCallback(async () => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    await flushTime(current);
    try {
      await api.post(`/exam/attempts/${attemptId}/submit`);
    } finally {
      navigate(`/exam/attempts/${attemptId}/results`, { replace: true });
    }
  }, [attemptId, current, flushTime, navigate]);

  if (error) return <div className="p-8 text-red-600">{error}</div>;
  if (!attempt) return <div className="p-8 text-slate-500">Loading exam...</div>;

  const deadline = new Date(attempt.started_at).getTime() + attempt.time_limit_minutes * 60 * 1000;
  const question = attempt.questions[current];
  const answeredCount = attempt.questions.filter((q) => q.given_answers.some((a) => a !== null)).length;
  const elapsedSeconds = Math.round((Date.now() - new Date(attempt.started_at).getTime()) / 1000);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-4 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-5 py-3 shadow-sm">
        <div>
          <PacingIndicator
            questionsAnswered={answeredCount}
            totalQuestions={attempt.questions.length}
            elapsedSeconds={elapsedSeconds}
            totalSeconds={attempt.time_limit_minutes * 60}
          />
          <p className="text-xs text-slate-400">{answeredCount} of {attempt.questions.length} answered</p>
        </div>
        <Countdown deadline={deadline} onExpire={doSubmit} />
      </div>

      {attempt.had_repeats && (
        <p className="mb-4 text-xs text-amber-600">
          Note: this exam includes some questions you've seen before — there weren't enough fresh ones in every topic.
        </p>
      )}

      <QuestionCard question={question} index={current} total={attempt.questions.length} onAnswer={handleAnswer} />

      <div className="mt-4 flex items-center justify-between">
        <button
          onClick={() => goTo(current - 1)}
          disabled={current === 0}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          Previous
        </button>
        {current < attempt.questions.length - 1 ? (
          <button
            onClick={() => goTo(current + 1)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Next
          </button>
        ) : (
          <button
            onClick={doSubmit}
            disabled={submitting}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit exam"}
          </button>
        )}
      </div>

      <div className="mt-6 flex flex-wrap gap-1.5">
        {attempt.questions.map((q) => (
          <button
            key={q.position}
            onClick={() => goTo(q.position)}
            className={`h-8 w-8 rounded text-xs font-medium ${
              q.position === current
                ? "bg-indigo-600 text-white"
                : q.given_answers.some((a) => a !== null)
                ? "bg-indigo-100 text-indigo-700"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {q.position + 1}
          </button>
        ))}
      </div>

      <div className="mt-6 text-center">
        <button onClick={doSubmit} disabled={submitting} className="text-sm text-slate-400 underline hover:text-slate-600">
          Submit now (even if not all questions are answered)
        </button>
      </div>
    </div>
  );
}
