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
    score: Math.round((scores[key] ?? 0) * 100),
    fullMark: 100,
  }));

  return (
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
        <Tooltip formatter={(v) => [`${v}점`, "감성 점수"]} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
