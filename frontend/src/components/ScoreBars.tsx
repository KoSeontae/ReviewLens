import { useState } from "react";
import { ALL_ASPECTS } from "../api";

const scoreColor = (score: number) => {
  if (score >= 0.75) return "bg-indigo-500";
  if (score >= 0.5) return "bg-yellow-400";
  return "bg-red-400";
};

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
    <div className="space-y-4">
      {hasAverages && (
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-full bg-indigo-500" /> 이 상품
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-1 bg-gray-400" /> 전체 평균
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
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-400">{label}</span>
                <span className="text-gray-300 text-xs">언급 없음</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5" />
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
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">{label}</span>
              <span className="text-gray-500">
                {pct}%
                {avgPct !== null && (
                  <span className="text-gray-400 ml-1 text-xs">(평균 {avgPct}%)</span>
                )}
              </span>
            </div>
            <div className="relative w-full bg-gray-100 rounded-full h-2.5">
              <div
                className={`${scoreColor(score)} h-2.5 rounded-full transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
              {avgPct !== null && (
                <div
                  className="absolute top-0 h-2.5 w-0.5 bg-gray-500 rounded"
                  style={{ left: `${avgPct}%` }}
                />
              )}
            </div>
            {hovered === key && summary && (
              <div className="mt-1.5 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 leading-relaxed">
                <span className="font-semibold text-gray-600">리뷰 요약 · </span>
                {summary}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
