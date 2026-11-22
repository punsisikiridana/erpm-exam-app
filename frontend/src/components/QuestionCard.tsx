import type { AttemptQuestion } from "../lib/api";

interface Props {
  question: AttemptQuestion;
  index: number;
  total: number;
  onAnswer: (answer: string) => void;
  showCorrectness?: boolean;
}

export function QuestionCard({ question, index, total, onAnswer, showCorrectness }: Props) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between text-sm text-slate-500">
        <span>
          Question {index + 1} of {total} {question.topic ? `· ${question.topic}` : ""}
        </span>
        <span className="uppercase tracking-wide">{question.qtype === "TF" ? "True / False" : "Single best answer"}</span>
      </div>
      <p className="mb-4 text-lg text-slate-900">{question.stem}</p>

      {question.qtype === "TF" ? (
        <div className="flex gap-3">
          {["True", "False"].map((opt) => (
            <button
              key={opt}
              onClick={() => onAnswer(opt)}
              className={`flex-1 rounded-md border px-4 py-3 text-left font-medium transition ${
                question.given_answer === opt
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-slate-200 hover:border-indigo-300"
              } ${
                showCorrectness && question.correct_answer === opt
                  ? "border-emerald-500 bg-emerald-50"
                  : showCorrectness && question.given_answer === opt && question.given_answer !== question.correct_answer
                  ? "border-red-500 bg-red-50"
                  : ""
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {(question.options ?? []).map((opt) => (
            <button
              key={opt.label}
              onClick={() => onAnswer(opt.label)}
              className={`rounded-md border px-4 py-3 text-left transition ${
                question.given_answer === opt.label
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-slate-200 hover:border-indigo-300"
              } ${
                showCorrectness && question.correct_answer === opt.label
                  ? "border-emerald-500 bg-emerald-50"
                  : showCorrectness && question.given_answer === opt.label && question.given_answer !== question.correct_answer
                  ? "border-red-500 bg-red-50"
                  : ""
              }`}
            >
              <span className="mr-2 font-semibold">{opt.label}.</span>
              {opt.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
