import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface TestTaker {
  id: number;
  name: string;
}

export function TestTakers() {
  const [takers, setTakers] = useState<TestTaker[]>([]);
  const [name, setName] = useState("");
  const [passcode, setPasscode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function load() {
    api
      .get<TestTaker[]>("/admin/testtakers")
      .then(setTakers)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) navigate("/admin/login");
      });
  }

  useEffect(load, [navigate]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/admin/testtakers", { name, passcode });
      setName("");
      setPasscode("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  async function remove(id: number) {
    try {
      await api.delete(`/admin/testtakers/${id}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Test-takers</h1>

      <form onSubmit={create} className="mb-6 flex gap-2">
        <input
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Passcode"
          value={passcode}
          onChange={(e) => setPasscode(e.target.value)}
          required
        />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Add</button>
      </form>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <div className="flex flex-col gap-2">
        {takers.map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <span>{t.name}</span>
            <button onClick={() => remove(t.id)} className="text-xs text-red-500 hover:underline">
              Remove
            </button>
          </div>
        ))}
        {takers.length === 0 && <p className="text-sm text-slate-400">No test-takers yet.</p>}
      </div>
    </div>
  );
}
