import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
} from "recharts";
import { ALL_ASPECTS } from "../api";
import { logVisit } from "../utils/tracking";

/* ── 스크롤 진입 페이드업 ── */
function useReveal(threshold = 0.12) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);
  return { ref, visible };
}

function Reveal({
  children, delay = 0, className, style,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(28px)",
        transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/* ── 데이터 ── */
const STATS = [
  { value: "13가지", label: "분석 속성" },
  { value: "4개",   label: "지원 쇼핑몰" },
  { value: "BERT",  label: "감성 분석 모델" },
  { value: "무료",  label: "회원가입 필요 없음" },
];

const STEPS = [
  {
    num: "01",
    title: "URL 붙여넣기",
    desc: "에이블리·무신사·지그재그·하이버 상품 페이지 URL을 그대로 붙여넣으세요.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
    ),
  },
  {
    num: "02",
    title: "리뷰 자동 수집",
    desc: "크롤러가 실구매자 리뷰를 자동으로 가져옵니다. 기다리기만 하면 돼요.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 16 12 12 8 16"/>
        <line x1="12" y1="12" x2="12" y2="21"/>
        <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
      </svg>
    ),
  },
  {
    num: "03",
    title: "속성별 분석 확인",
    desc: "AI가 13가지 항목별 감성 점수와 요약 문장을 레이더·막대 차트로 보여줍니다.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
    ),
  },
];

const USE_CASES = [
  {
    emoji: "📏",
    title: "사이즈가 걱정될 때",
    desc: "사이즈·핏 점수와 실구매자 체형 데이터를 확인해 내 몸에 맞는 사이즈를 예측할 수 있어요.",
    tags: ["사이즈", "핏"],
  },
  {
    emoji: "🧵",
    title: "소재가 궁금할 때",
    desc: "소재·비침·신축성·계절감 점수로 실제 입었을 때 느낌을 구매 전에 파악할 수 있어요.",
    tags: ["소재", "비침", "신축성"],
  },
  {
    emoji: "⚖️",
    title: "여러 상품을 비교할 때",
    desc: "각 상품의 속성 점수를 전체 평균과 비교해 어떤 상품이 실제로 더 나은지 확인해요.",
    tags: ["전체 평균 비교"],
  },
];

const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
      </svg>
    ),
    title: "13가지 속성 분석",
    desc: "핏·소재·마감·착용감 등 패션에서 중요한 13가지 항목별로 리뷰를 분류하고 감성 점수를 산출합니다.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
      </svg>
    ),
    title: "4개 쇼핑몰 지원",
    desc: "에이블리·무신사·지그재그·하이버 URL을 붙여넣기만 하면 리뷰를 자동 수집합니다.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
      </svg>
    ),
    title: "AI 키워드 요약",
    desc: "단순 별점이 아닌 BERT 기반 모델이 리뷰 문장을 읽고 속성별 요약 문장을 함께 제공합니다.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="3"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/><path d="M18 8h4M20 6v4"/>
      </svg>
    ),
    title: "나만의 종합 점수",
    desc: "관심 속성마다 중요도(1~5)를 직접 설정하면, 내 기준으로 가중 평균한 종합 점수를 바로 확인할 수 있습니다.",
  },
];

const SAMPLE_SCORES = [
  { key: "fit",      label: "핏",     score: 88 },
  { key: "material", label: "소재",   score: 74 },
  { key: "size",     label: "사이즈", score: 91 },
  { key: "price",    label: "가격",   score: 62 },
  { key: "design",   label: "디자인", score: 83 },
  { key: "comfort",  label: "착용감", score: 79 },
  { key: "delivery", label: "배송",   score: 95 },
  { key: "color",    label: "색상",   score: 68 },
];

function scoreColor(score: number) {
  if (score >= 80) return { color: "#059669", bg: "#ecfdf5" };
  if (score >= 65) return { color: "#7c3aed", bg: "#f5f3ff" };
  if (score >= 50) return { color: "#d97706", bg: "#fffbeb" };
  return { color: "#dc2626", bg: "#fef2f2" };
}

const SHOPS = ["에이블리", "무신사", "지그재그", "하이버"];

const CARD_STYLE: React.CSSProperties = {
  background: "rgba(255,255,255,0.75)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(139,92,246,0.1)",
  boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
};

/* ── 페이지 ── */
export default function Landing() {
  useEffect(() => { logVisit(); }, []);

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(160deg, #f0edff 0%, #faf9ff 50%, #ede9fe 100%)" }}>
      {/* 배경 블롭 */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div style={{ position: "absolute", top: 0, right: 0, width: 520, height: 520, borderRadius: "50%", background: "radial-gradient(circle, rgba(167,139,250,0.2) 0%, transparent 70%)", transform: "translate(30%,-30%)" }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(196,181,253,0.15) 0%, transparent 70%)", transform: "translate(-30%,30%)" }} />
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-5 py-20 flex flex-col gap-20">

        {/* ── 히어로 ── */}
        <section className="text-center flex flex-col items-center gap-5">
          <Reveal delay={0}>
            <span
              className="text-5xl font-extrabold tracking-tight"
              style={{ background: "linear-gradient(135deg, #6d28d9 0%, #a855f7 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}
            >
              ReviewLens
            </span>
          </Reveal>
          <Reveal delay={120}>
            <p className="text-lg font-medium leading-relaxed" style={{ color: "#3d3960" }}>
              패션 리뷰를 <span style={{ color: "#7c3aed", fontWeight: 700 }}>13가지 속성</span>으로 분석해<br />
              상품의 진짜 평판을 한눈에 보여드립니다
            </p>
          </Reveal>
          <Reveal delay={240}>
            <div className="flex gap-2 flex-wrap justify-center">
              {SHOPS.map((s) => (
                <span key={s} className="text-xs font-semibold px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(124,58,237,0.08)", color: "#7c3aed", border: "1px solid rgba(124,58,237,0.18)" }}>
                  {s}
                </span>
              ))}
            </div>
          </Reveal>
        </section>

        {/* ── C. 숫자로 보는 ReviewLens ── */}
        <section>
          <Reveal delay={0}>
            <p className="text-xs font-semibold mb-5 text-center" style={{ color: "#9d98b8", letterSpacing: "0.1em" }}>
              숫자로 보는 ReviewLens
            </p>
          </Reveal>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {STATS.map((s, i) => (
              <Reveal key={s.label} delay={i * 80}>
                <div className="rounded-2xl p-5 text-center" style={CARD_STYLE}>
                  <p className="text-2xl font-extrabold mb-1" style={{ color: "#7c3aed" }}>{s.value}</p>
                  <p className="text-xs" style={{ color: "#9d98b8" }}>{s.label}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── A. 사용 방법 ── */}
        <section>
          <Reveal delay={0}>
            <p className="text-xs font-semibold mb-5 text-center" style={{ color: "#9d98b8", letterSpacing: "0.1em" }}>
              사용 방법
            </p>
          </Reveal>
          <div className="flex flex-col gap-3">
            {STEPS.map((step, i) => (
              <Reveal key={step.num} delay={i * 100}>
                <div className="rounded-2xl p-5 flex items-start gap-4" style={CARD_STYLE}>
                  <div className="flex-shrink-0 flex flex-col items-center gap-2">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.08)", color: "#7c3aed" }}>
                      {step.icon}
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className="w-px flex-1 min-h-4" style={{ background: "rgba(124,58,237,0.15)" }} />
                    )}
                  </div>
                  <div className="pt-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold" style={{ color: "#c4b5fd" }}>{step.num}</span>
                      <p className="text-sm font-bold" style={{ color: "#1a1a2e" }}>{step.title}</p>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: "#7c6fa0" }}>{step.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── B. 이런 분들께 유용해요 ── */}
        <section>
          <Reveal delay={0}>
            <p className="text-xs font-semibold mb-5 text-center" style={{ color: "#9d98b8", letterSpacing: "0.1em" }}>
              이런 분들께 유용해요
            </p>
          </Reveal>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {USE_CASES.map((uc, i) => (
              <Reveal key={uc.title} delay={i * 100}>
                <div className="rounded-2xl p-5 flex flex-col gap-3 h-full" style={CARD_STYLE}>
                  <span className="text-2xl">{uc.emoji}</span>
                  <p className="text-sm font-bold" style={{ color: "#1a1a2e" }}>{uc.title}</p>
                  <p className="text-xs leading-relaxed flex-1" style={{ color: "#7c6fa0" }}>{uc.desc}</p>
                  <div className="flex flex-wrap gap-1.5 pt-1" style={{ borderTop: "1px solid rgba(139,92,246,0.08)" }}>
                    {uc.tags.map((t) => (
                      <span key={t} className="text-xs px-2 py-0.5 rounded-full"
                        style={{ background: "rgba(124,58,237,0.08)", color: "#7c3aed", border: "1px solid rgba(124,58,237,0.15)" }}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── 기능 카드 ── */}
        <section>
          <Reveal delay={0}>
            <p className="text-xs font-semibold mb-5 text-center" style={{ color: "#9d98b8", letterSpacing: "0.1em" }}>
              주요 기능
            </p>
          </Reveal>
          <div className="grid grid-cols-2 gap-3">
            {FEATURES.map((f, i) => (
              <Reveal key={f.title} delay={i * 100}>
                <div className="rounded-2xl p-5 flex flex-col gap-3 h-full" style={CARD_STYLE}>
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.08)", color: "#7c3aed" }}>
                    {f.icon}
                  </div>
                  <p className="text-sm font-bold" style={{ color: "#1a1a2e" }}>{f.title}</p>
                  <p className="text-xs leading-relaxed" style={{ color: "#7c6fa0" }}>{f.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── 점수 계산 기준 ── */}
        <section>
          <Reveal delay={0}>
            <p className="text-xs font-semibold mb-5 text-center" style={{ color: "#9d98b8", letterSpacing: "0.1em" }}>
              점수는 어떻게 계산되나요?
            </p>
          </Reveal>
          <div className="flex flex-col gap-3">
            {/* 계산 방식 3단계 */}
            <Reveal delay={0}>
              <div className="rounded-2xl p-5" style={CARD_STYLE}>
                <p className="text-sm font-bold mb-4" style={{ color: "#1a1a2e" }}>채점 방식</p>
                <div className="flex flex-col gap-3">
                  {[
                    { num: "1", text: "리뷰 문장을 \"핏감\", \"소재\", \"배송\" 등 속성 키워드 기준으로 분류합니다." },
                    { num: "2", text: "KLUE-BERT AI 모델이 각 문장의 감성을 60가지 감정 레이블로 분류합니다." },
                    { num: "3", text: "긍정 감정 비율을 0~100점으로 환산해 속성별 평균을 냅니다." },
                  ].map((step) => (
                    <div key={step.num} className="flex gap-3 items-start">
                      <span
                        className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5"
                        style={{ background: "rgba(124,58,237,0.12)", color: "#7c3aed" }}
                      >
                        {step.num}
                      </span>
                      <p className="text-xs leading-relaxed" style={{ color: "#7c6fa0" }}>{step.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>

            {/* 점수 등급 범례 */}
            <Reveal delay={100}>
              <div className="rounded-2xl p-5" style={CARD_STYLE}>
                <p className="text-sm font-bold mb-4" style={{ color: "#1a1a2e" }}>점수 등급</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {[
                    { range: "80 ~ 100", label: "매우 긍정",  color: "#059669", bg: "#ecfdf5" },
                    { range: "65 ~ 79",  label: "양호",       color: "#7c3aed", bg: "#f5f3ff" },
                    { range: "50 ~ 64",  label: "보통",       color: "#d97706", bg: "#fffbeb" },
                    { range: "0 ~ 49",   label: "부정",  color: "#dc2626", bg: "#fef2f2" },
                  ].map((g) => (
                    <div
                      key={g.label}
                      className="rounded-xl p-3 text-center"
                      style={{ background: g.bg, border: `1px solid ${g.color}22` }}
                    >
                      <p className="text-sm font-extrabold" style={{ color: g.color }}>{g.range}</p>
                      <p className="text-xs mt-0.5" style={{ color: g.color, opacity: 0.75 }}>{g.label}</p>
                    </div>
                  ))}
                </div>
                <p className="text-xs mt-3" style={{ color: "#bdb8d4" }}>
                  * 리뷰에서 해당 속성이 언급되지 않으면 점수가 산출되지 않습니다.
                </p>
              </div>
            </Reveal>
          </div>
        </section>

        {/* ── 화면 구성 미리보기 ── */}
        <Reveal delay={0}>
          <div className="rounded-2xl p-5" style={CARD_STYLE}>
            <p className="text-sm font-bold mb-1" style={{ color: "#1a1a2e" }}>실제 화면 구성</p>
            <p className="text-xs mb-4" style={{ color: "#9d98b8" }}>관심 속성과 중요도를 설정하면 나만의 종합 점수가 계산됩니다</p>

            {/* 관심 속성 + 중요도 */}
            <div className="rounded-xl p-4 mb-3" style={{ background: "#faf8ff", border: "1px solid rgba(139,92,246,0.08)" }}>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-semibold" style={{ color: "#6d28d9" }}>관심 속성</p>
                <span className="text-xs" style={{ color: "#bdb8d4" }}>4 / 13</span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {[
                  { label: "핏",     active: true,  dot: "#7c3aed" },
                  { label: "소재",   active: true,  dot: "#059669" },
                  { label: "사이즈", active: false },
                  { label: "가격",   active: true,  dot: "#d97706" },
                  { label: "배송",   active: false },
                  { label: "디자인", active: true,  dot: "#059669" },
                ].map(({ label, active, dot }) => (
                  <span
                    key={label}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
                    style={
                      active
                        ? { background: "rgba(124,58,237,0.1)", border: "1.5px solid rgba(124,58,237,0.35)", color: "#6d28d9" }
                        : { background: "#f5f3ff", border: "1.5px solid #e5e0f5", color: "#9d98b8" }
                    }
                  >
                    {dot && <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: dot }} />}
                    {label}
                  </span>
                ))}
              </div>

              <div style={{ borderTop: "1px solid rgba(139,92,246,0.08)", marginBottom: "10px" }} />

              <p className="text-xs font-semibold mb-2" style={{ color: "#9d98b8" }}>중요도</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                {[
                  { label: "핏",     w: 4 },
                  { label: "소재",   w: 5 },
                  { label: "가격",   w: 3 },
                  { label: "디자인", w: 5 },
                ].map(({ label, w }) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className="text-xs font-medium w-12 flex-shrink-0" style={{ color: "#3d3960" }}>{label}</span>
                    <div className="flex gap-1.5">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <div key={n} className="w-3 h-3 rounded-full" style={{ background: n <= w ? "#7c3aed" : "#e5e0f5" }} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 종합 점수 카드 */}
            <div className="rounded-xl p-4 text-center" style={{ background: "#ecfdf5", border: "1px solid #05966922" }}>
              <div className="text-4xl font-extrabold" style={{ color: "#059669" }}>87</div>
              <div className="text-sm font-semibold mt-1" style={{ color: "#059669", opacity: 0.85 }}>나의 종합 점수</div>
              <div className="text-xs mt-0.5" style={{ color: "#9d98b8" }}>관심 속성 가중 평균 · 4개 항목</div>
            </div>
          </div>
        </Reveal>

        {/* ── 속성 점수 미리보기 ── */}
        <Reveal delay={0}>
          <div className="rounded-2xl p-6" style={CARD_STYLE}>
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-bold" style={{ color: "#1a1a2e" }}>속성별 점수 예시</p>
              <span className="text-xs px-2.5 py-1 rounded-full font-medium"
                style={{ background: "rgba(124,58,237,0.08)", color: "#7c3aed" }}>
                샘플 데이터
              </span>
            </div>
            <p className="text-xs mb-5" style={{ color: "#9d98b8" }}>실제 분석 결과는 이런 형태로 제공됩니다</p>

            {/* 레이더 차트 */}
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={SAMPLE_SCORES.map(({ label, score }) => ({ subject: label, score, fullMark: 100 }))}>
                <PolarGrid stroke="rgba(139,92,246,0.12)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "#7c6fa0", fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar dataKey="score" stroke="#7c3aed" fill="rgba(124,58,237,0.15)" strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>

            <div className="my-4" style={{ borderTop: "1px solid rgba(139,92,246,0.08)" }} />

            {/* 막대 차트 */}
            <div className="space-y-3">
              {SAMPLE_SCORES.map(({ key, label, score }) => {
                const { color, bg } = scoreColor(score);
                return (
                  <div key={key} className="flex items-center gap-3">
                    <span className="text-xs font-medium w-14 flex-shrink-0" style={{ color: "#3d3960" }}>{label}</span>
                    <div className="flex-1 rounded-full h-2" style={{ background: "#f0ecff" }}>
                      <div className="h-2 rounded-full" style={{ width: `${score}%`, background: "linear-gradient(to right, #6d28d9, #a78bfa)" }} />
                    </div>
                    <span className="text-xs font-bold w-9 text-right px-1.5 py-0.5 rounded-lg"
                      style={{ color, background: bg, flexShrink: 0 }}>
                      {score}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="mt-5 pt-4 flex flex-wrap gap-1.5" style={{ borderTop: "1px solid rgba(139,92,246,0.08)" }}>
              {ALL_ASPECTS.map(({ key, label }) => (
                <span key={key} className="text-xs px-2.5 py-1 rounded-full"
                  style={{ background: "#f5f3ff", color: "#7c6fa0", border: "1px solid #e5e0f5" }}>
                  {label}
                </span>
              ))}
            </div>
          </div>
        </Reveal>

        {/* ── 하단 CTA ── */}
        <Reveal delay={0}>
          <div className="text-center">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-2xl font-bold text-sm transition-all duration-200"
              style={{
                background: "linear-gradient(135deg, #7c3aed 0%, #9333ea 100%)",
                color: "#fff",
                boxShadow: "0 6px 28px rgba(124,58,237,0.3)",
              }}
            >
              지금 분석 시작하기
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
          </div>
        </Reveal>

      </div>
    </div>
  );
}
