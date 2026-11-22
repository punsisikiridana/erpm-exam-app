import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type AttemptSummary, type ExamTemplateSummary } from "../../lib/api";

export function ExamHome() {
  const [templates, setTemplates] = useState<ExamTemplateSummary[]>([]);
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([api.get<ExamTemplateSummary[]>("/exam/templates"), api.get<AttemptSummary[]>("/exam/attempts")])
      .then(([t, a]) => {
        setTemplates(t);
        setAttempts(a);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          navigate("/exam/login");
        } else {
          setError("Failed to load exams");
        }
      });
  }, [navigate]);

  async function startExam(templateId: number) {
    setStarting(templateId);
    setError(null);
    try {
      const attempt = await api.post<{ id: number }>("/exam/attempts", { exam_template_id: templateId });
      navigate(`/exam/attempts/${attempt.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start exam");
      setStarting(null);
    }
  }

  const unsubmitted = attempts.filter((a) => !a.submitted_at);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">ERPM Practice Exams</h1>

      {unsubmitted.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-2 text-lg font-medium text-slate-800">Resume in-progress</h2>
          <div className="flex flex-col gap-2">
            {unsubmitted.map((a) => (
              <button
                key={a.id}
                onClick={() => navigate(`/exam/attempts/${a.id}`)}
                className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-left hover:bg-amber-100"
              >
                {a.template_name} — started {new Date(a.started_at).toLocaleString()}
              </button>
            ))}
          </div>
        </div>
      )}

      <h2 className="mb-2 text-lg font-medium text-slate-800">Available exams</h2>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      <div className="flex flex-col gap-3">
        {templates.map((t) => (
          <div key={t.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-1 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">{t.name}</h3>
              <span className="text-sm text-slate-500">{t.time_limit_minutes} min</span>
            </div>
            <p className="mb-3 text-sm text-slate-500">
              {t.total_questions} questions · {t.topics.map((topic) => topic.topic_name).join(" + ")}
            </p>
            <button
              onClick={() => startExam(t.id)}
              disabled={starting === t.id}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {starting === t.id ? "Starting..." : "Start exam"}
            </button>
          </div>
        ))}
        {templates.length === 0 && <p className="text-sm text-slate-500">No exam templates have been set up yet.</p>}
      </div>

      {attempts.filter((a) => a.submitted_at).length > 0 && (
        <div className="mt-8">
          <h2 className="mb-2 text-lg font-medium text-slate-800">Past attempts</h2>
          <div className="flex flex-col gap-2">
            {attempts
              .filter((a) => a.submitted_at)
              .map((a) => (
                <button
                  key={a.id}
                  onClick={() => navigate(`/exam/attempts/${a.id}/results`)}
                  className="rounded-md border border-slate-200 bg-white px-4 py-3 text-left hover:border-indigo-300"
                >
                  {a.template_name} — {a.score}/{a.total_questions} — {new Date(a.submitted_at!).toLocaleString()}
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
