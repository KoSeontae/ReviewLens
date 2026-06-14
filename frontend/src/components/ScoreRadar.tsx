import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
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
}

export default function ScoreRadar({ scores }: Props) {
  const data = Object.entries(LABELS).map(([key, label]) => ({
    subject: label,
    score: key in scores ? Math.round(scores[key] * 100) : null,
    fullMark: 100,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis domain={[0, 100]} tick={false} />
          <Radar
            name="감성 점수"
            dataKey="score"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.4}
          />
          <Tooltip
            formatter={(v) => v === null ? ["데이터 없음", ""] : [`${v}점`, "감성 점수"]}
          />
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
