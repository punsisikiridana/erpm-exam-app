import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { QuestionCard } from "../../components/QuestionCard";
import { api, ApiError, type ResultQuestion } from "../../lib/api";

interface ResultsData {
  id: number;
  score: number;
  total_marks: number;
  total_questions: number;
  auto_submitted: boolean;
  questions: ResultQuestion[];
}

export function Results() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ResultsData>(`/exam/attempts/${attemptId}/results`)
      .then(setData)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/exam/login");
        else setError("Could not load results");
      });
  }, [attemptId, navigate]);

  if (error) return <div className="p-8 text-red-600">{error}</div>;
  if (!data) return <div className="p-8 text-slate-500">Loading results...</div>;

  const pct = data.total_marks > 0 ? Math.round((data.score / data.total_marks) * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8 rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
        <p className="text-sm text-slate-500">Your score</p>
        <p className="text-4xl font-bold text-slate-900">
          {data.score} / {data.total_marks}
        </p>
        <p className="text-sm text-slate-500">
          {pct}% &middot; {data.total_questions} questions
        </p>
        {data.auto_submitted && <p className="mt-2 text-xs text-amber-600">Auto-submitted when time ran out.</p>}
        <button
          onClick={() => navigate("/exam")}
          className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Back to exams
        </button>
      </div>

      <h2 className="mb-3 text-lg font-medium text-slate-800">Review</h2>
      <div className="flex flex-col gap-4">
        {data.questions.map((q) => (
          <div key={q.position}>
            <div className="mb-1 flex justify-end">
              <span className="text-xs font-medium text-slate-400">
                {q.score_achieved} / {q.max_score} marks &middot; {q.time_spent_seconds}s
              </span>
            </div>
            <QuestionCard question={q} index={q.position} total={data.total_questions} onAnswer={() => {}} showCorrectness />
          </div>
        ))}
      </div>
    </div>
  );
}
