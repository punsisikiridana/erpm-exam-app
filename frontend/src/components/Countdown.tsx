import { useEffect, useState } from "react";

interface Props {
  deadline: number; // epoch ms
  onExpire: () => void;
}

export function Countdown({ deadline, onExpire }: Props) {
  const [remainingMs, setRemainingMs] = useState(deadline - Date.now());

  useEffect(() => {
    const tick = () => {
      const remaining = deadline - Date.now();
      setRemainingMs(remaining);
      if (remaining <= 0) onExpire();
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [deadline, onExpire]);

  const totalSeconds = Math.max(0, Math.floor(remainingMs / 1000));
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const low = totalSeconds < 5 * 60;

  return (
    <div className={`font-mono text-2xl font-bold tabular-nums ${low ? "text-red-600" : "text-slate-800"}`}>
      {h > 0 ? `${h}:` : ""}
      {String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
    </div>
  );
}
