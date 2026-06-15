import { useState } from "react";
import { ALL_ASPECTS } from "../api";

function barGradient(score: number): string {
  if (score >= 0.75) return "linear-gradient(to right, #6d28d9, #a78bfa)";
  if (score >= 0.5) return "linear-gradient(to right, #b45309, #fbbf24)";
  return "linear-gradient(to right, #b91c1c, #f87171)";
}

function scoreColor(score: number): string {
  if (score >= 0.75) return "#7c3aed";
  if (score >= 0.5) return "#d97706";
  return "#dc2626";
}

interface Props {
  scores: Record<string, number>;
  averages?: Record<string, number>;
  summaries?: Record<string, string> | null;
  visibleAspects: string[];
}

export default function ScoreBars({ scores, averages = {}, summaries, visibleAspects }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);
  const hasAverages = Object.keys(averages).length > 0;
  const aspects = ALL_ASPECTS.filter((a) => visibleAspects.includes(a.key));

  return (
    <div className="space-y-5">
      {hasAverages && (
        <div className="flex items-center gap-4 text-xs" style={{ color: "#9d98b8" }}>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#7c3aed" }} />
            이 상품
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-0.5 rounded" style={{ background: "#c4b5fd" }} />
            전체 평균
          </span>
        </div>
      )}

      {aspects.map(({ key, label }) => {
        const score = scores[key];
        const avg = averages[key];
        const summary = summaries?.[key];

        if (score === undefined) {
          return (
            <div key={key}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium" style={{ color: "#bdb8d4" }}>{label}</span>
                <span className="text-xs" style={{ color: "#d4d0e8" }}>언급 없음</span>
              </div>
              <div className="w-full rounded-full h-2" style={{ background: "#f0ecff" }} />
            </div>
          );
        }

        const pct = Math.round(score * 100);
        const avgPct = avg !== undefined ? Math.round(avg * 100) : null;

        return (
          <div
            key={key}
            className="relative"
            onMouseEnter={() => setHovered(key)}
            onMouseLeave={() => setHovered(null)}
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium" style={{ color: "#3d3960" }}>{label}</span>
              <div className="flex items-center gap-2">
                {avgPct !== null && (
                  <span className="text-xs" style={{ color: "#bdb8d4" }}>평균 {avgPct}</span>
                )}
                <span className="text-sm font-bold tabular-nums" style={{ color: scoreColor(score) }}>
                  {pct}
                </span>
              </div>
            </div>

            <div className="relative w-full rounded-full h-2" style={{ background: "#f0ecff" }}>
              <div
                className="h-2 rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, background: barGradient(score) }}
              />
              {avgPct !== null && (
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-0.5 h-3.5 rounded-full"
                  style={{ left: `${avgPct}%`, background: "#c4b5fd" }}
                />
              )}
            </div>

            {hovered === key && summary && (
              <div
                className="mt-2 text-xs leading-relaxed px-3 py-2.5 rounded-xl"
                style={{
                  color: "#7c6fa0",
                  background: "rgba(124,58,237,0.05)",
                  border: "1px solid rgba(124,58,237,0.15)",
                }}
              >
                {summary}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
