import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type Question, type QuestionType, type Subject } from "../../lib/api";

const OPTION_LABELS = ["A", "B", "C", "D", "E"];

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
  const [optionTexts, setOptionTexts] = useState<Record<string, string>>({});
  const [correctAnswer, setCorrectAnswer] = useState("");
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

  async function createQuestion(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!topicId) {
      setError("Pick a topic");
      return;
    }
    const options = qtype === "SBA" ? OPTION_LABELS.map((label) => ({ label, text: optionTexts[label] ?? "" })) : undefined;
    try {
      await api.post("/admin/questions", {
        topic_id: topicId,
        qtype,
        stem,
        options,
        correct_answer: correctAnswer,
        explanation: explanation || null,
        source: "manual",
      });
      setStem("");
      setOptionTexts({});
      setCorrectAnswer("");
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
            onChange={(e) => setQtype(e.target.value as QuestionType)}
          >
            <option value="TF">True / False</option>
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
        {qtype === "SBA" ? (
          <div className="mb-3 flex flex-col gap-2">
            {OPTION_LABELS.map((label) => (
              <div key={label} className="flex items-center gap-2">
                <span className="w-5 text-sm font-semibold">{label}.</span>
                <input
                  className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
                  value={optionTexts[label] ?? ""}
                  onChange={(e) => setOptionTexts((prev) => ({ ...prev, [label]: e.target.value }))}
                  placeholder={`Option ${label}`}
                />
              </div>
            ))}
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={correctAnswer}
              onChange={(e) => setCorrectAnswer(e.target.value)}
              required
            >
              <option value="">Correct answer...</option>
              {OPTION_LABELS.map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <select
            className="mb-3 rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={correctAnswer}
            onChange={(e) => setCorrectAnswer(e.target.value)}
            required
          >
            <option value="">Correct answer...</option>
            <option value="True">True</option>
            <option value="False">False</option>
          </select>
        )}
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
                {q.qtype} · <span className={q.source === "mcqmed" ? "text-indigo-600" : "text-slate-400"}>{q.source}</span>
              </span>
              <button onClick={() => deleteQuestion(q.id)} className="text-red-500 hover:underline">
                Delete
              </button>
            </div>
            <p className="text-sm text-slate-900">{q.stem}</p>
            <p className="mt-1 text-xs text-emerald-600">Correct: {q.correct_answer}</p>
          </div>
        ))}
        {questions.length === 0 && <p className="text-sm text-slate-400">No questions found.</p>}
      </div>
    </div>
  );
}
