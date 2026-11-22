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

export interface QuestionPart {
  order: number;
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: number;
  topic_id: number;
  qtype: QuestionType;
  stem: string;
  parts: QuestionPart[];
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

// A part as shown during the attempt: no correctness revealed yet.
export interface AttemptPart {
  order: number;
  text: string;
}

export interface AttemptQuestion {
  position: number;
  qtype: QuestionType;
  stem: string;
  parts: AttemptPart[];
  given_answers: (boolean | null)[];
  max_score: number;
  time_spent_seconds: number;
  topic?: string;
}

export interface Attempt {
  id: number;
  started_at: string;
  submitted_at: string | null;
  auto_submitted: boolean;
  had_repeats: boolean;
  time_limit_minutes: number;
  total_questions: number;
  total_marks: number;
  score: number | null;
  questions: AttemptQuestion[];
}

export interface AttemptSummary {
  id: number;
  template_name: string;
  started_at: string;
  submitted_at: string | null;
  score: number | null;
  total_marks: number;
  total_questions: number;
  test_taker_name?: string;
  auto_submitted?: boolean;
  had_repeats?: boolean;
}

// A part as shown on the results/review page: correctness revealed.
export interface ResultPart {
  order: number;
  text: string;
  is_correct: boolean;
  given: boolean | null;
}

export interface ResultQuestion {
  position: number;
  qtype: QuestionType;
  stem: string;
  parts: ResultPart[];
  score_achieved: number | null;
  max_score: number;
  time_spent_seconds: number;
  topic?: string;
}
