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
}

export default function ScoreBars({ scores }: Props) {
  return (
    <div className="space-y-3">
      {Object.entries(LABELS).map(([key, label]) => {
        const score = scores[key];
        if (score === undefined) return null;
        const pct = Math.round(score * 100);
        return (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">{label}</span>
              <span className="text-gray-500">{pct}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2.5">
              <div
                className={`${scoreColor(score)} h-2.5 rounded-full transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
