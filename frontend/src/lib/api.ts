const BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { ApiError };

// ---- Types ----

export type QuestionType = "TF" | "SBA";

export interface Topic {
  id: number;
  name: string;
}

export interface Subject {
  id: number;
  name: string;
  topics: Topic[];
}

export interface QuestionOption {
  label: string;
  text: string;
}

export interface Question {
  id: number;
  topic_id: number;
  qtype: QuestionType;
  stem: string;
  options: QuestionOption[] | null;
  correct_answer: string;
  explanation: string | null;
  source: "mcqmed" | "manual";
  source_external_id: string | null;
}

export interface ExamTemplateRule {
  topic_id: number;
  tf_count: number;
  sba_count: number;
  order: number;
}

export interface ExamTemplate {
  id: number;
  name: string;
  time_limit_minutes: number;
  is_preset: boolean;
  rules: ExamTemplateRule[];
}

export interface ExamTemplateSummary {
  id: number;
  name: string;
  time_limit_minutes: number;
  total_questions: number;
  topics: { topic_name: string; tf_count: number; sba_count: number }[];
}

export interface AttemptQuestion {
  position: number;
  qtype: QuestionType;
  stem: string;
  options: QuestionOption[] | null;
  given_answer: string | null;
  is_correct: boolean | null;
  time_spent_seconds: number;
  topic?: string;
  correct_answer?: string;
}

export interface Attempt {
  id: number;
  started_at: string;
  submitted_at: string | null;
  auto_submitted: boolean;
  had_repeats: boolean;
  time_limit_minutes: number;
  total_questions: number;
  score: number | null;
  questions: AttemptQuestion[];
}

export interface AttemptSummary {
  id: number;
  template_name: string;
  started_at: string;
  submitted_at: string | null;
  score: number | null;
  total_questions: number;
  test_taker_name?: string;
  auto_submitted?: boolean;
  had_repeats?: boolean;
}
