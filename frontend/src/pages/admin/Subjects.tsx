import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type Subject } from "../../lib/api";

export function Subjects() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newTopicName, setNewTopicName] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function load() {
    api
      .get<Subject[]>("/admin/subjects")
      .then(setSubjects)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }

  useEffect(load, [navigate]);

  async function addSubject(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/admin/subjects", { name: newSubjectName });
      setNewSubjectName("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  async function addTopic(subjectId: number) {
    const name = newTopicName[subjectId];
    if (!name) return;
    try {
      await api.post("/admin/topics", { subject_id: subjectId, name });
      setNewTopicName((prev) => ({ ...prev, [subjectId]: "" }));
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  async function deleteTopic(topicId: number) {
    try {
      await api.delete(`/admin/topics/${topicId}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  async function deleteSubject(subjectId: number) {
    try {
      await api.delete(`/admin/subjects/${subjectId}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Subjects & Topics</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <form onSubmit={addSubject} className="mb-6 flex gap-2">
        <input
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="New subject name (e.g. Medicine)"
          value={newSubjectName}
          onChange={(e) => setNewSubjectName(e.target.value)}
          required
        />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Add subject</button>
      </form>

      <div className="flex flex-col gap-4">
        {subjects.map((s) => (
          <div key={s.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">{s.name}</h2>
              <button onClick={() => deleteSubject(s.id)} className="text-xs text-red-500 hover:underline">
                Delete subject
              </button>
            </div>
            <ul className="mb-2 flex flex-col gap-1">
              {s.topics.map((t) => (
                <li key={t.id} className="flex items-center justify-between rounded bg-slate-50 px-3 py-1.5 text-sm">
                  <span>{t.name}</span>
                  <button onClick={() => deleteTopic(t.id)} className="text-xs text-red-500 hover:underline">
                    Delete
                  </button>
                </li>
              ))}
              {s.topics.length === 0 && <li className="text-sm text-slate-400">No topics yet</li>}
            </ul>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
                placeholder="New topic name (e.g. Cardiology)"
                value={newTopicName[s.id] ?? ""}
                onChange={(e) => setNewTopicName((prev) => ({ ...prev, [s.id]: e.target.value }))}
              />
              <button
                onClick={() => addTopic(s.id)}
                className="rounded-md border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50"
              >
                Add topic
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
