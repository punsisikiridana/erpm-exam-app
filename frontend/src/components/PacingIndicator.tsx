interface Props {
  questionsAnswered: number;
  totalQuestions: number;
  elapsedSeconds: number;
  totalSeconds: number;
}

export function PacingIndicator({ questionsAnswered, totalQuestions, elapsedSeconds, totalSeconds }: Props) {
  const expectedProgress = totalSeconds > 0 ? elapsedSeconds / totalSeconds : 0;
  const actualProgress = totalQuestions > 0 ? questionsAnswered / totalQuestions : 0;
  const diff = actualProgress - expectedProgress;

  const budgetPerQuestion = totalQuestions > 0 ? totalSeconds / totalQuestions : 0;

  let label = "On pace";
  let color = "text-slate-500";
  if (diff < -0.08) {
    label = "Behind pace";
    color = "text-amber-600";
  } else if (diff > 0.08) {
    label = "Ahead of pace";
    color = "text-emerald-600";
  }

  return (
    <div className="text-sm">
      <span className={`font-medium ${color}`}>{label}</span>
      <span className="text-slate-400"> · ~{Math.round(budgetPerQuestion)}s/question budget</span>
    </div>
  );
}
