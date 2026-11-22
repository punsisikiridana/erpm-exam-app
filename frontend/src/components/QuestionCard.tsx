import type { AttemptQuestion, ResultQuestion } from "../lib/api";

interface Props {
  question: AttemptQuestion | ResultQuestion;
  index: number;
  total: number;
  onAnswer: (givenAnswers: (boolean | null)[]) => void;
  showCorrectness?: boolean;
}

function isResultQuestion(q: AttemptQuestion | ResultQuestion): q is ResultQuestion {
  return (q as ResultQuestion).parts.length > 0 && "is_correct" in q.parts[0];
}

export function QuestionCard({ question, index, total, onAnswer, showCorrectness }: Props) {
  const given: (boolean | null)[] = isResultQuestion(question)
    ? question.parts.map((p) => p.given)
    : (question as AttemptQuestion).given_answers;

  function setPart(partIndex: number, value: boolean) {
    if (question.qtype === "SBA") {
      // only one part can be selected
      const next = question.parts.map((_, i) => (i === partIndex ? true : null));
      onAnswer(next);
    } else {
      const next = [...given];
      next[partIndex] = value;
      onAnswer(next);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between text-sm text-slate-500">
        <span>
          Question {index + 1} of {total} {question.topic ? `· ${question.topic}` : ""}
        </span>
        <span className="uppercase tracking-wide">
          {question.qtype === "TF" ? "True / False (each statement)" : "Single best answer"}
        </span>
      </div>
      <p className="mb-4 text-lg text-slate-900">{question.stem}</p>

      <div className="flex flex-col gap-2">
        {question.parts.map((part, i) => {
          const value = given[i];
          const resultPart = isResultQuestion(question) ? question.parts[i] : undefined;

          // SBA: always show the correct option in green (it's the answer key,
          // regardless of what was picked), and the user's wrong pick in red.
          const sbaCorrectOption = showCorrectness && resultPart?.is_correct;
          const sbaWrongPick = showCorrectness && resultPart && value !== null && value !== resultPart.is_correct;

          // T/F: each statement is an independent judgment, so highlight based
          // on whether the user's True/False call matched reality — not on
          // whether the statement itself happens to be true.
          const tfCorrectCall = showCorrectness && resultPart && value !== null && value === resultPart.is_correct;
          const tfWrongCall = showCorrectness && resultPart && value !== null && value !== resultPart.is_correct;

          if (question.qtype === "SBA") {
            return (
              <button
                key={i}
                onClick={() => setPart(i, true)}
                className={`rounded-md border px-4 py-3 text-left transition ${
                  value === true ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 hover:border-indigo-300"
                } ${sbaCorrectOption ? "border-emerald-500 bg-emerald-50" : sbaWrongPick ? "border-red-500 bg-red-50" : ""}`}
              >
                <span className="mr-2 font-semibold">{String.fromCharCode(65 + i)}.</span>
                {part.text}
              </button>
            );
          }

          return (
            <div
              key={i}
              className={`flex items-center justify-between rounded-md border px-4 py-2.5 ${
                tfCorrectCall ? "border-emerald-400 bg-emerald-50" : tfWrongCall ? "border-red-400 bg-red-50" : "border-slate-200"
              }`}
            >
              <span className="mr-4 flex-1 text-slate-800">{part.text}</span>
              <div className="flex gap-1.5">
                {["True", "False"].map((label) => {
                  const asBool = label === "True";
                  return (
                    <button
                      key={label}
                      onClick={() => setPart(i, asBool)}
                      className={`rounded px-3 py-1 text-sm font-medium ${
                        value === asBool ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
