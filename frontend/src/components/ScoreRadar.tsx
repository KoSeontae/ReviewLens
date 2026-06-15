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
import { ALL_ASPECTS } from "../api";

interface Props {
  scores: Record<string, number>;
  averages?: Record<string, number>;
  summaries?: Record<string, string> | null;
  visibleAspects: string[];
}

interface TooltipPayload {
  name: string;
  value: number | null;
  payload: { key: string };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  summaries?: Record<string, string> | null;
}

function CustomTooltip({ active, payload, summaries }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const key = payload[0]?.payload?.key;
  const summary = key && summaries?.[key];

  return (
    <div
      className="rounded-xl p-3 text-sm max-w-xs"
      style={{
        background: "#fff",
        border: "1px solid rgba(124,58,237,0.15)",
        boxShadow: "0 8px 24px rgba(109,40,217,0.12)",
      }}
    >
      {payload.map((p) => (
        <div key={p.name} className="flex items-center justify-between gap-4">
          <span style={{ color: "#9d98b8", fontSize: 12 }}>{p.name}</span>
          <span className="font-bold" style={{ color: p.name === "이 상품" ? "#7c3aed" : "#bdb8d4" }}>
            {p.value === null ? "—" : `${p.value}점`}
          </span>
        </div>
      ))}
      {summary && (
        <div
          className="mt-2 pt-2 text-xs leading-relaxed"
          style={{ borderTop: "1px solid #f0ecff", color: "#7c6fa0" }}
        >
          {summary}
        </div>
      )}
    </div>
  );
}

export default function ScoreRadar({ scores, averages = {}, summaries, visibleAspects }: Props) {
  const hasAverages = Object.keys(averages).length > 0;
  const aspects = ALL_ASPECTS.filter((a) => visibleAspects.includes(a.key));

  const data = aspects.map(({ key, label }) => ({
    subject: label,
    key,
    score: key in scores ? Math.round(scores[key] * 100) : null,
    average: key in averages ? Math.round(averages[key] * 100) : null,
    fullMark: 100,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(139,92,246,0.12)" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: "#7c6fa0", fontSize: 11 }}
          />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          {hasAverages && (
            <Radar
              name="전체 평균"
              dataKey="average"
              stroke="#c4b5fd"
              fill="rgba(196,181,253,0.15)"
              strokeDasharray="4 3"
              strokeWidth={1.5}
            />
          )}
          <Radar
            name="이 상품"
            dataKey="score"
            stroke="#7c3aed"
            fill="rgba(124,58,237,0.15)"
            strokeWidth={2}
          />
          <Tooltip content={<CustomTooltip summaries={summaries} />} />
          {hasAverages && (
            <Legend
              wrapperStyle={{ fontSize: 12, color: "#9d98b8", paddingTop: 8 }}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
      {aspects.some(({ key }) => !(key in scores)) && (
        <p className="text-xs text-center mt-1" style={{ color: "#bdb8d4" }}>
          * 리뷰에서 언급되지 않은 속성은 표시되지 않습니다
        </p>
      )}
    </div>
  );
}
