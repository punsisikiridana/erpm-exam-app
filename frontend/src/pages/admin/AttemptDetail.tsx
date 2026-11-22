import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface TopicBreakdown {
  score_achieved: number;
  max_score: number;
  time_spent_seconds: number;
}

interface DetailPart {
  order: number;
  text: string;
  is_correct: boolean;
  given: boolean | null;
}

interface DetailQuestion {
  position: number;
  topic: string;
  qtype: "TF" | "SBA";
  stem: string;
  parts: DetailPart[];
  score_achieved: number;
  max_score: number;
  time_spent_seconds: number;
}

interface Detail {
  id: number;
  test_taker_name: string;
  template_name: string;
  score: number;
  total_marks: number;
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
        Score {data.score}/{data.total_marks} ({data.total_questions} questions) · {data.time_limit_minutes} min limit
        {data.auto_submitted ? " · auto-submitted" : ""}
        {data.had_repeats ? " · had repeat questions" : ""}
      </p>

      <h2 className="mb-2 font-medium text-slate-800">Per-topic breakdown</h2>
      <div className="mb-6 flex flex-col gap-1">
        {Object.entries(data.per_topic_breakdown).map(([topic, b]) => (
          <div key={topic} className="flex justify-between rounded bg-white px-3 py-2 text-sm shadow-sm">
            <span>{topic}</span>
            <span>
              {b.score_achieved}/{b.max_score} marks · {Math.round(b.time_spent_seconds / 60)} min spent
            </span>
          </div>
        ))}
      </div>

      <h2 className="mb-2 font-medium text-slate-800">Questions</h2>
      <div className="flex flex-col gap-2">
        {data.questions.map((q) => (
          <div
            key={q.position}
            className={`rounded-lg border p-3 text-sm shadow-sm ${
              q.score_achieved === q.max_score ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"
            }`}
          >
            <p className="mb-1 text-xs text-slate-500">
              {q.topic} · {q.score_achieved}/{q.max_score} marks · {q.time_spent_seconds}s spent
            </p>
            <p className="mb-1 text-slate-900">{q.stem}</p>
            <ul className="text-xs">
              {q.parts.map((p, i) => (
                <li key={i} className={p.given === p.is_correct ? "text-emerald-700" : "text-red-700"}>
                  {p.text} — correct: <strong>{String(p.is_correct)}</strong>, given:{" "}
                  <strong>{p.given === null ? "(none)" : String(p.given)}</strong>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
