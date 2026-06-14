import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const LABELS: Record<string, string> = {
  fit: "핏",
  material: "소재",
  finish: "마감",
  size: "사이즈",
  price: "가격",
};

interface Props {
  scores: Record<string, number>;
  averages?: Record<string, number>;
}

export default function ScoreRadar({ scores, averages = {} }: Props) {
  const hasAverages = Object.keys(averages).length > 0;

  const data = Object.entries(LABELS).map(([key, label]) => ({
    subject: label,
    score: key in scores ? Math.round(scores[key] * 100) : null,
    average: key in averages ? Math.round(averages[key] * 100) : null,
    fullMark: 100,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis domain={[0, 100]} tick={false} />
          {hasAverages && (
            <Radar
              name="전체 평균"
              dataKey="average"
              stroke="#9ca3af"
              fill="#9ca3af"
              fillOpacity={0.15}
              strokeDasharray="4 3"
            />
          )}
          <Radar
            name="이 상품"
            dataKey="score"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.4}
          />
          <Tooltip
            formatter={(v, name) =>
              v === null ? ["데이터 없음", name] : [`${v}점`, name]
            }
          />
          {hasAverages && <Legend />}
        </RadarChart>
      </ResponsiveContainer>
      {Object.entries(LABELS).some(([key]) => !(key in scores)) && (
        <p className="text-xs text-gray-400 text-center mt-1">
          * 리뷰에서 언급되지 않은 속성은 차트에 표시되지 않습니다
        </p>
      )}
    </div>
  );
}
