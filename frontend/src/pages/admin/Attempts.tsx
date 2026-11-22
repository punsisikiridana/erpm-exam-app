import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type AttemptSummary } from "../../lib/api";

export function Attempts() {
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get<AttemptSummary[]>("/admin/attempts")
      .then(setAttempts)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }, [navigate]);

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Attempts</h1>
      <div className="flex flex-col gap-2">
        {attempts.map((a) => (
          <button
            key={a.id}
            onClick={() => navigate(`/admin/attempts/${a.id}`)}
            className="rounded-lg border border-slate-200 bg-white p-4 text-left shadow-sm hover:border-indigo-300"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">
                {a.test_taker_name} — {a.template_name}
              </span>
              <span className="text-sm text-slate-500">
                {a.submitted_at ? `${a.score}/${a.total_marks}` : "In progress"}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Started {new Date(a.started_at).toLocaleString()}
              {a.auto_submitted ? " · auto-submitted" : ""}
              {a.had_repeats ? " · had repeat questions" : ""}
            </p>
          </button>
        ))}
        {attempts.length === 0 && <p className="text-sm text-slate-400">No attempts yet.</p>}
      </div>
    </div>
  );
}
