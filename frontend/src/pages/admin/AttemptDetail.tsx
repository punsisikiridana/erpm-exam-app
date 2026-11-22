import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface TopicBreakdown {
  correct: number;
  total: number;
  time_spent_seconds: number;
}

interface DetailQuestion {
  position: number;
  topic: string;
  stem: string;
  given_answer: string | null;
  correct_answer: string;
  is_correct: boolean | null;
  time_spent_seconds: number;
}

interface Detail {
  id: number;
  test_taker_name: string;
  template_name: string;
  score: number;
  total_questions: number;
  time_limit_minutes: number;
  auto_submitted: boolean;
  had_repeats: boolean;
  per_topic_breakdown: Record<string, TopicBreakdown>;
  questions: DetailQuestion[];
}

export function AttemptDetail() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<Detail | null>(null);

  useEffect(() => {
    api
      .get<Detail>(`/admin/attempts/${attemptId}`)
      .then(setData)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }, [attemptId, navigate]);

  if (!data) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <div>
      <button onClick={() => navigate("/admin/attempts")} className="mb-4 text-sm text-slate-400 hover:text-slate-600">
        ← Back to attempts
      </button>
      <h1 className="mb-1 text-xl font-semibold text-slate-900">
        {data.test_taker_name} — {data.template_name}
      </h1>
      <p className="mb-4 text-sm text-slate-500">
        Score {data.score}/{data.total_questions} · {data.time_limit_minutes} min limit
        {data.auto_submitted ? " · auto-submitted" : ""}
        {data.had_repeats ? " · had repeat questions" : ""}
      </p>

      <h2 className="mb-2 font-medium text-slate-800">Per-topic breakdown</h2>
      <div className="mb-6 flex flex-col gap-1">
        {Object.entries(data.per_topic_breakdown).map(([topic, b]) => (
          <div key={topic} className="flex justify-between rounded bg-white px-3 py-2 text-sm shadow-sm">
            <span>{topic}</span>
            <span>
              {b.correct}/{b.total} correct · {Math.round(b.time_spent_seconds / 60)} min spent
            </span>
          </div>
        ))}
      </div>

      <h2 className="mb-2 font-medium text-slate-800">Questions</h2>
      <div className="flex flex-col gap-2">
        {data.questions.map((q) => (
          <div
            key={q.position}
            className={`rounded-lg border p-3 text-sm shadow-sm ${q.is_correct ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"}`}
          >
            <p className="mb-1 text-xs text-slate-500">
              {q.topic} · {q.time_spent_seconds}s spent
            </p>
            <p className="mb-1 text-slate-900">{q.stem}</p>
            <p className="text-xs">
              Given: <strong>{q.given_answer ?? "(none)"}</strong> · Correct: <strong>{q.correct_answer}</strong>
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
