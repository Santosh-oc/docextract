import { useEffect, useState } from "react";

const STAGES = [
  "Preparing PDF...",
  "Rendering PDF pages...",
  "Sending document to Vision Model...",
  "Processing extraction...",
  "Validating results...",
];

/** Mount this only while an extraction request is in flight (e.g.
 * `{extracting && <ExtractionProgress />}`) — a fresh mount is what starts it
 * at stage 0 each time, so there is no need to reset state via an effect. */
export default function ExtractionProgress() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGES.length - 1));
    }, 1400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <ol className="space-y-2">
        {STAGES.map((stage, i) => (
          <li key={stage} className="flex items-center gap-2 text-sm">
            <span
              className={`h-2 w-2 flex-none rounded-full ${
                i < stageIndex
                  ? "bg-emerald-500"
                  : i === stageIndex
                    ? "animate-pulse bg-slate-900 dark:bg-slate-100"
                    : "bg-slate-200 dark:bg-slate-700"
              }`}
            />
            <span
              className={
                i <= stageIndex
                  ? "text-slate-900 dark:text-slate-100"
                  : "text-slate-400 dark:text-slate-600"
              }
            >
              {stage}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
