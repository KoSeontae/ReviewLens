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
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-sm max-w-xs">
      {payload.map((p) => (
        <div key={p.name} className="text-gray-700">
          <span className="font-semibold">{p.name}: </span>
          {p.value === null ? "데이터 없음" : `${p.value}점`}
        </div>
      ))}
      {summary && (
        <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500 leading-relaxed">
          <span className="font-semibold text-gray-600">리뷰 요약 · </span>
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
          <Tooltip content={<CustomTooltip summaries={summaries} />} />
          {hasAverages && <Legend />}
        </RadarChart>
      </ResponsiveContainer>
      {aspects.some(({ key }) => !(key in scores)) && (
        <p className="text-xs text-gray-400 text-center mt-1">
          * 리뷰에서 언급되지 않은 속성은 차트에 표시되지 않습니다
        </p>
      )}
    </div>
  );
}
