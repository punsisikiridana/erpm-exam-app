import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type Question, type QuestionType, type Subject } from "../../lib/api";

interface PartDraft {
  text: string;
  is_correct: boolean;
}

function defaultParts(qtype: QuestionType): PartDraft[] {
  if (qtype === "SBA") {
    return Array.from({ length: 5 }, () => ({ text: "", is_correct: false }));
  }
  return Array.from({ length: 5 }, () => ({ text: "", is_correct: false }));
}

export function Questions() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [topicFilter, setTopicFilter] = useState<number | "">("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const [topicId, setTopicId] = useState<number | "">("");
  const [qtype, setQtype] = useState<QuestionType>("TF");
  const [stem, setStem] = useState("");
  const [parts, setParts] = useState<PartDraft[]>(defaultParts("TF"));
  const [explanation, setExplanation] = useState("");

  const allTopics = useMemo(() => subjects.flatMap((s) => s.topics.map((t) => ({ ...t, subjectName: s.name }))), [subjects]);

  function loadQuestions() {
    const params = new URLSearchParams();
    if (topicFilter) params.set("topic_id", String(topicFilter));
    if (search) params.set("search", search);
    api
      .get<Question[]>(`/admin/questions?${params.toString()}`)
      .then(setQuestions)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }

  useEffect(() => {
    api.get<Subject[]>("/admin/subjects").then(setSubjects);
  }, []);

  useEffect(loadQuestions, [topicFilter, search]); // eslint-disable-line react-hooks/exhaustive-deps

  function changeQtype(next: QuestionType) {
    setQtype(next);
    setParts(defaultParts(next));
  }

  function updatePartText(i: number, text: string) {
    setParts((prev) => prev.map((p, idx) => (idx === i ? { ...p, text } : p)));
  }

  function setPartCorrect(i: number, checked: boolean) {
    setParts((prev) =>
      prev.map((p, idx) => {
        if (qtype === "SBA") return { ...p, is_correct: idx === i };
        return idx === i ? { ...p, is_correct: checked } : p;
      })
    );
  }

  function addPart() {
    setParts((prev) => [...prev, { text: "", is_correct: false }]);
  }

  function removePart(i: number) {
    setParts((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function createQuestion(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!topicId) {
      setError("Pick a topic");
      return;
    }
    const filledParts = parts.filter((p) => p.text.trim());
    if (filledParts.length < 2) {
      setError("Add at least 2 parts/options");
      return;
    }
    if (qtype === "SBA" && filledParts.filter((p) => p.is_correct).length !== 1) {
      setError("SBA needs exactly one correct option");
      return;
    }
    try {
      await api.post("/admin/questions", {
        topic_id: topicId,
        qtype,
        stem,
        parts: filledParts.map((p, i) => ({ order: i + 1, text: p.text, is_correct: p.is_correct })),
        explanation: explanation || null,
        source: "manual",
      });
      setStem("");
      setParts(defaultParts(qtype));
      setExplanation("");
      loadQuestions();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create question");
    }
  }

  async function deleteQuestion(id: number) {
    try {
      await api.delete(`/admin/questions/${id}`);
      loadQuestions();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Questions</h1>

      <form onSubmit={createQuestion} className="mb-8 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 font-medium text-slate-800">Add a question manually</h2>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        <div className="mb-3 flex gap-2">
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={topicId}
            onChange={(e) => setTopicId(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Topic...</option>
            {allTopics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.subjectName} / {t.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={qtype}
            onChange={(e) => changeQtype(e.target.value as QuestionType)}
          >
            <option value="TF">True / False (multi-statement)</option>
            <option value="SBA">Single-best-answer</option>
          </select>
        </div>
        <textarea
          className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Question stem"
          value={stem}
          onChange={(e) => setStem(e.target.value)}
          required
        />
        <p className="mb-1 text-xs text-slate-500">
          {qtype === "TF"
            ? "Each statement below is marked True or False independently (like the real exam)."
            : "Mark exactly one option as correct."}
        </p>
        <div className="mb-3 flex flex-col gap-2">
          {parts.map((part, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type={qtype === "SBA" ? "radio" : "checkbox"}
                name="correct-part"
                checked={part.is_correct}
                onChange={(e) => setPartCorrect(i, e.target.checked)}
                title={qtype === "SBA" ? "Correct option" : "True"}
              />
              <input
                className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
                value={part.text}
                onChange={(e) => updatePartText(i, e.target.value)}
                placeholder={qtype === "SBA" ? `Option ${String.fromCharCode(65 + i)}` : `Statement ${i + 1}`}
              />
              {parts.length > 2 && (
                <button type="button" onClick={() => removePart(i)} className="text-xs text-red-500 hover:underline">
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addPart} className="self-start text-sm text-indigo-600 hover:underline">
            + Add {qtype === "SBA" ? "option" : "statement"}
          </button>
        </div>
        <textarea
          className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Explanation (optional)"
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
        />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Add question</button>
      </form>

      <div className="mb-3 flex gap-2">
        <select
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value ? Number(e.target.value) : "")}
        >
          <option value="">All topics</option>
          {allTopics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.subjectName} / {t.name}
            </option>
          ))}
        </select>
        <input
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Search question text..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-2">
        {questions.map((q) => (
          <div key={q.id} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
              <span>
                {q.qtype} · {q.parts.length} parts ·{" "}
                <span className={q.source === "mcqmed" ? "text-indigo-600" : "text-slate-400"}>{q.source}</span>
              </span>
              <button onClick={() => deleteQuestion(q.id)} className="text-red-500 hover:underline">
                Delete
              </button>
            </div>
            <p className="text-sm text-slate-900">{q.stem}</p>
            <ul className="mt-1 text-xs text-slate-500">
              {q.parts.map((p, i) => (
                <li key={i} className={p.is_correct ? "text-emerald-600" : ""}>
                  {p.is_correct ? "✓" : "·"} {p.text}
                </li>
              ))}
            </ul>
          </div>
        ))}
        {questions.length === 0 && <p className="text-sm text-slate-400">No questions found.</p>}
      </div>
    </div>
  );
}
