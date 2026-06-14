const LABELS: Record<string, string> = {
  fit: "핏",
  material: "소재",
  finish: "마감",
  size: "사이즈",
  price: "가격",
};

const scoreColor = (score: number) => {
  if (score >= 0.75) return "bg-indigo-500";
  if (score >= 0.5) return "bg-yellow-400";
  return "bg-red-400";
};

interface Props {
  scores: Record<string, number>;
  averages?: Record<string, number>;
}

export default function ScoreBars({ scores, averages = {} }: Props) {
  const hasAverages = Object.keys(averages).length > 0;

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
      {Object.entries(LABELS).map(([key, label]) => {
        const score = scores[key];
        const avg = averages[key];

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
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">{label}</span>
              <span className="text-gray-500">
                {pct}%
                {avgPct !== null && (
                  <span className="text-gray-400 ml-1 text-xs">
                    (평균 {avgPct}%)
                  </span>
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
          </div>
        );
      })}
    </div>
  );
}
