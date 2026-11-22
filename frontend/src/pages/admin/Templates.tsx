import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type ExamTemplate, type Subject } from "../../lib/api";

const PRESETS = [
  { label: "Standard paper — 25 T/F + 25 SBA, 125 min", tf: 25, sba: 25, minutes: 125 },
  { label: "Psychiatry/Community/Forensic — 20 T/F + 15 SBA, 90 min", tf: 20, sba: 15, minutes: 90 },
  { label: "Custom", tf: 0, sba: 0, minutes: 60 },
];

interface RuleRow {
  topic_id: number | "";
  tf_count: number;
  sba_count: number;
}

export function Templates() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [templates, setTemplates] = useState<ExamTemplate[]>([]);
  const [name, setName] = useState("");
  const [presetIndex, setPresetIndex] = useState(0);
  const [timeLimit, setTimeLimit] = useState(PRESETS[0].minutes);
  const [rules, setRules] = useState<RuleRow[]>([{ topic_id: "", tf_count: PRESETS[0].tf, sba_count: PRESETS[0].sba }]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const allTopics = useMemo(() => subjects.flatMap((s) => s.topics.map((t) => ({ ...t, subjectName: s.name }))), [subjects]);

  function load() {
    api
      .get<ExamTemplate[]>("/admin/templates")
      .then(setTemplates)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }

  useEffect(() => {
    api.get<Subject[]>("/admin/subjects").then(setSubjects);
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function applyPreset(index: number) {
    setPresetIndex(index);
    const preset = PRESETS[index];
    setTimeLimit(preset.minutes);
    setRules((prev) => (prev.length ? prev.map((r) => ({ ...r, tf_count: preset.tf, sba_count: preset.sba })) : prev));
  }

  function addRuleRow() {
    const preset = PRESETS[presetIndex];
    setRules((prev) => [...prev, { topic_id: "", tf_count: preset.tf, sba_count: preset.sba }]);
  }

  function updateRule(index: number, patch: Partial<RuleRow>) {
    setRules((prev) => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  function removeRule(index: number) {
    setRules((prev) => prev.filter((_, i) => i !== index));
  }

  async function createTemplate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (rules.some((r) => !r.topic_id)) {
      setError("Every rule needs a topic selected");
      return;
    }
    try {
      await api.post("/admin/templates", {
        name,
        time_limit_minutes: timeLimit,
        rules: rules.map((r, i) => ({ topic_id: r.topic_id, tf_count: r.tf_count, sba_count: r.sba_count, order: i })),
      });
      setName("");
      setRules([{ topic_id: "", tf_count: PRESETS[presetIndex].tf, sba_count: PRESETS[presetIndex].sba }]);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create template");
    }
  }

  async function deleteTemplate(id: number) {
    try {
      await api.delete(`/admin/templates/${id}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Exam Templates</h1>

      <form onSubmit={createTemplate} className="mb-8 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 font-medium text-slate-800">Create a template</h2>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        <input
          className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Template name (e.g. Medicine - Cardiology full paper)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <div className="mb-3 flex items-center gap-2">
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={presetIndex}
            onChange={(e) => applyPreset(Number(e.target.value))}
          >
            {PRESETS.map((p, i) => (
              <option key={p.label} value={i}>
                {p.label}
              </option>
            ))}
          </select>
          <label className="text-sm text-slate-600">
            Time limit:
            <input
              type="number"
              className="ml-2 w-20 rounded-md border border-slate-300 px-2 py-1 text-sm"
              value={timeLimit}
              onChange={(e) => setTimeLimit(Number(e.target.value))}
            />
            min
          </label>
        </div>

        <div className="mb-3 flex flex-col gap-2">
          {rules.map((rule, i) => (
            <div key={i} className="flex items-center gap-2">
              <select
                className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
                value={rule.topic_id}
                onChange={(e) => updateRule(i, { topic_id: e.target.value ? Number(e.target.value) : "" })}
              >
                <option value="">Topic...</option>
                {allTopics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.subjectName} / {t.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                className="w-16 rounded-md border border-slate-300 px-2 py-1 text-sm"
                value={rule.tf_count}
                onChange={(e) => updateRule(i, { tf_count: Number(e.target.value) })}
                title="T/F count"
              />
              <span className="text-xs text-slate-400">T/F</span>
              <input
                type="number"
                className="w-16 rounded-md border border-slate-300 px-2 py-1 text-sm"
                value={rule.sba_count}
                onChange={(e) => updateRule(i, { sba_count: Number(e.target.value) })}
                title="SBA count"
              />
              <span className="text-xs text-slate-400">SBA</span>
              {rules.length > 1 && (
                <button type="button" onClick={() => removeRule(i)} className="text-xs text-red-500 hover:underline">
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addRuleRow} className="self-start text-sm text-indigo-600 hover:underline">
            + Add another topic to mix in
          </button>
        </div>

        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Create template</button>
      </form>

      <div className="flex flex-col gap-2">
        {templates.map((t) => (
          <div key={t.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-1 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">{t.name}</h3>
              <button onClick={() => deleteTemplate(t.id)} className="text-xs text-red-500 hover:underline">
                Delete
              </button>
            </div>
            <p className="text-sm text-slate-500">{t.time_limit_minutes} min</p>
            <ul className="mt-1 text-sm text-slate-600">
              {t.rules.map((r, i) => {
                const topic = allTopics.find((top) => top.id === r.topic_id);
                return (
                  <li key={i}>
                    {topic ? `${topic.subjectName} / ${topic.name}` : `Topic ${r.topic_id}`}: {r.tf_count} T/F + {r.sba_count} SBA
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
        {templates.length === 0 && <p className="text-sm text-slate-400">No templates yet.</p>}
      </div>
    </div>
  );
}
