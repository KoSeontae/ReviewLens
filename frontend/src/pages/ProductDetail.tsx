import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import { api, ALL_ASPECTS } from "../api";
import type { Product, AnalysisResult, Review, Source, FitRecommendation } from "../api";
import ScoreRadar from "../components/ScoreRadar";
import ScoreBars from "../components/ScoreBars";

type Tab = "radar" | "bars" | "reviews";

const SOURCE_LABELS: Record<Source, string> = {
  ably: "에이블리",
  musinsa: "무신사",
  zigzag: "지그재그",
  hiver: "하이버",
};

const STORAGE_KEY = "reviewlens_visible_aspects";
const WEIGHTS_KEY  = "reviewlens_aspect_weights";

function loadVisibleAspects(): string[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return ["fit", "material", "finish", "size", "price"];
}

function saveVisibleAspects(keys: string[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

function loadAspectWeights(): Record<string, number> {
  try {
    const saved = localStorage.getItem(WEIGHTS_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return {};
}

function saveAspectWeights(weights: Record<string, number>) {
  localStorage.setItem(WEIGHTS_KEY, JSON.stringify(weights));
}

const BODY_KEY = "reviewlens_body_info";

function loadBodyInfo(): { height: string; weight: string } {
  try {
    const saved = localStorage.getItem(BODY_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return { height: "", weight: "" };
}

function saveBodyInfo(info: { height: string; weight: string }) {
  localStorage.setItem(BODY_KEY, JSON.stringify(info));
}

function scoreGrade(score: number): { color: string; bg: string } {
  if (score >= 0.8) return { color: "#059669", bg: "#ecfdf5" };
  if (score >= 0.65) return { color: "#7c3aed", bg: "#f5f3ff" };
  if (score >= 0.5) return { color: "#d97706", bg: "#fffbeb" };
  return { color: "#dc2626", bg: "#fef2f2" };
}

export default function ProductDetail() {
  const { source, code } = useParams<{ source: Source; code: string }>();
  const { pathname } = useLocation();
  const [product, setProduct] = useState<Product | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [averages, setAverages] = useState<Record<string, number>>({});
  const [visibleAspects, setVisibleAspects] = useState<string[]>(loadVisibleAspects);
  const [aspectWeights, setAspectWeights] = useState<Record<string, number>>(loadAspectWeights);
  const [bodyInfo, setBodyInfo] = useState(loadBodyInfo);
  const [fitResult, setFitResult] = useState<FitRecommendation | null>(null);
  const [fitLoading, setFitLoading] = useState(false);
  const [fitError, setFitError] = useState("");
  const [tab, setTab] = useState<Tab>("radar");
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!source || !code) return;
    api.getProduct(source, code).then(setProduct).catch(() => setError("상품 정보를 불러올 수 없습니다."));
    api.getAnalysis(source, code).then(setAnalysis).catch(() => {});
    api.getReviews(source, code).then(setReviews).catch(() => {});
    api.getAverages().then(setAverages).catch(() => {});
  }, [source, code]);

  const setWeight = (key: string, value: number) => {
    setAspectWeights((prev) => {
      const next = { ...prev, [key]: value };
      saveAspectWeights(next);
      return next;
    });
  };

  const runFitRecommendation = async () => {
    if (!source || !code) return;
    const height = Number(bodyInfo.height);
    const weight = Number(bodyInfo.weight);
    if (!height || !weight) {
      setFitError("키와 몸무게를 모두 입력해주세요.");
      return;
    }
    setFitLoading(true);
    setFitError("");
    try {
      const result = await api.getFitRecommendation(source, code, height, weight);
      setFitResult(result);
    } catch {
      setFitError("추천을 불러오는 데 실패했습니다.");
    } finally {
      setFitLoading(false);
    }
  };

  const toggleAspect = (key: string) => {
    setVisibleAspects((prev) => {
      const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key];
      saveVisibleAspects(next);
      return next;
    });
  };

  const runAnalysis = async () => {
    if (!source || !code) return;
    setAnalyzing(true);
    setProgress(null);
    setError("");

    const pollId = setInterval(async () => {
      try {
        const p = await api.getAnalyzeProgress(source, code);
        if (p.total > 0) setProgress({ done: p.done, total: p.total });
      } catch {}
    }, 800);

    try {
      const result = await api.analyze(source, code);
      const updatedReviews = await api.getReviews(source, code);
      setAnalysis(result);
      setReviews(updatedReviews);
    } catch {
      setError("분석 중 오류가 발생했습니다.");
    } finally {
      clearInterval(pollId);
      setAnalyzing(false);
      setProgress(null);
    }
  };

  if (!product) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: "linear-gradient(160deg, #f0edff 0%, #faf9ff 50%, #ede9fe 100%)" }}
      >
        {error ? (
          <p style={{ color: "#dc2626" }}>{error}</p>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin w-6 h-6" viewBox="0 0 24 24" fill="none" style={{ color: "#7c3aed" }}>
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <span className="text-sm" style={{ color: "#7c6fa0" }}>불러오는 중…</span>
          </div>
        )}
      </div>
    );
  }

  const scoredVisible = analysis
    ? visibleAspects.filter((k) => analysis.scores[k] !== undefined)
    : [];
  const totalWeight = scoredVisible.reduce((s, k) => s + (aspectWeights[k] ?? 3), 0);
  const weightedScore =
    analysis && totalWeight > 0
      ? Math.round(
          scoredVisible.reduce(
            (s, k) => s + (aspectWeights[k] ?? 3) * (analysis.scores[k] * 100),
            0
          ) / totalWeight
        )
      : null;
  const weightedGrade = weightedScore !== null ? scoreGrade(weightedScore / 100) : null;

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(160deg, #f0edff 0%, #faf9ff 60%, #ede9fe 100%)" }}>
      {/* 헤더 */}
      <header
        className="sticky top-0 z-50 px-5 py-3 flex items-center gap-3"
        style={{
          background: "rgba(245,244,255,0.85)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(139,92,246,0.1)",
          boxShadow: "0 1px 12px rgba(109,40,217,0.06)",
        }}
      >
        <Link
          to="/app"
          className="flex items-center gap-1.5 text-sm font-medium transition-colors duration-150"
          style={{ color: "#7c3aed" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          홈
        </Link>
        <span
          className="text-xs font-semibold px-2.5 py-1 rounded-full"
          style={{ background: "rgba(124,58,237,0.1)", color: "#7c3aed", border: "1px solid rgba(124,58,237,0.2)" }}
        >
          {SOURCE_LABELS[product.source as Source]}
        </span>
        <span className="text-sm truncate flex-1" style={{ color: "#4a4560" }}>
          {product.name}
        </span>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* 상품 카드 */}
        <div
          className="rounded-2xl overflow-hidden flex gap-0"
          style={{
            background: "rgba(255,255,255,0.8)",
            border: "1px solid rgba(139,92,246,0.1)",
            boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
          }}
        >
          {product.image_url && (
            <div
              className="flex-shrink-0"
              style={{ width: 120, height: 120, background: "#f5f3ff" }}
            >
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          <div className="px-5 py-4 flex flex-col justify-center">
            {product.brand && (
              <p className="text-xs font-bold mb-1" style={{ color: "#7c3aed" }}>
                {product.brand}
              </p>
            )}
            <h2 className="text-sm font-bold leading-snug" style={{ color: "#1a1a2e" }}>
              {product.name}
            </h2>
            <p className="text-xs mt-2" style={{ color: "#9d98b8" }}>
              리뷰 {reviews.length}개 수집됨
            </p>
          </div>
        </div>

        {/* 관심 속성 선택 */}
        <div
          className="rounded-2xl p-4 space-y-3"
          style={{
            background: "rgba(255,255,255,0.8)",
            border: "1px solid rgba(139,92,246,0.1)",
            boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
          }}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold" style={{ color: "#6d28d9", letterSpacing: "0.06em" }}>
              관심 속성
            </p>
            <span className="text-xs" style={{ color: "#bdb8d4" }}>
              {visibleAspects.length} / {ALL_ASPECTS.length}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {ALL_ASPECTS.map(({ key, label }) => {
              const active = visibleAspects.includes(key);
              const score = analysis?.scores[key];
              const grade = score !== undefined ? scoreGrade(score) : null;
              return (
                <button
                  key={key}
                  onClick={() => toggleAspect(key)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-150"
                  style={
                    active
                      ? {
                          background: "rgba(124,58,237,0.1)",
                          border: "1.5px solid rgba(124,58,237,0.35)",
                          color: "#6d28d9",
                        }
                      : {
                          background: "#f5f3ff",
                          border: "1.5px solid #e5e0f5",
                          color: "#9d98b8",
                        }
                  }
                >
                  {grade && (
                    <span
                      className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                      style={{ background: active ? grade.color : "#d4d0e8" }}
                    />
                  )}
                  {label}
                </button>
              );
            })}
          </div>

          {visibleAspects.length > 0 && (
            <>
              <div style={{ borderTop: "1px solid rgba(139,92,246,0.08)" }} />
              <div>
                <p className="text-xs font-semibold mb-2.5" style={{ color: "#9d98b8", letterSpacing: "0.05em" }}>
                  중요도
                </p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                  {visibleAspects.map((key) => {
                    const aspect = ALL_ASPECTS.find((a) => a.key === key);
                    const w = aspectWeights[key] ?? 3;
                    return (
                      <div key={key} className="flex items-center gap-3">
                        <span className="text-xs font-medium w-14 flex-shrink-0" style={{ color: "#3d3960" }}>
                          {aspect?.label ?? key}
                        </span>
                        <div className="flex gap-1.5">
                          {[1, 2, 3, 4, 5].map((n) => (
                            <button
                              key={n}
                              onClick={() => setWeight(key, n)}
                              className="w-3.5 h-3.5 rounded-full transition-all duration-150"
                              style={{ background: n <= w ? "#7c3aed" : "#e5e0f5" }}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* 체형 유사 리뷰 추천 */}
        <div
          className="rounded-2xl p-4 space-y-3"
          style={{
            background: "rgba(255,255,255,0.8)",
            border: "1px solid rgba(139,92,246,0.1)",
            boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
          }}
        >
          <div>
            <p className="text-xs font-semibold" style={{ color: "#6d28d9", letterSpacing: "0.06em" }}>
              내 체형과 비슷한 리뷰 추천
            </p>
            <p className="text-xs mt-1" style={{ color: "#9d98b8" }}>
              키/몸무게를 입력하면 비슷한 체형 구매자들의 사이즈·핏 만족도를 보여드려요
            </p>
          </div>

          <div className="flex gap-2">
            <input
              type="number"
              placeholder="키 (cm)"
              value={bodyInfo.height}
              onChange={(e) => {
                const next = { ...bodyInfo, height: e.target.value };
                setBodyInfo(next);
                saveBodyInfo(next);
                setFitError("");
              }}
              className="flex-1 rounded-xl px-3 py-2 text-sm outline-none"
              style={{ background: "#faf8ff", border: "1.5px solid rgba(109,40,217,0.15)", color: "#1a1a2e" }}
            />
            <input
              type="number"
              placeholder="몸무게 (kg)"
              value={bodyInfo.weight}
              onChange={(e) => {
                const next = { ...bodyInfo, weight: e.target.value };
                setBodyInfo(next);
                saveBodyInfo(next);
                setFitError("");
              }}
              className="flex-1 rounded-xl px-3 py-2 text-sm outline-none"
              style={{ background: "#faf8ff", border: "1.5px solid rgba(109,40,217,0.15)", color: "#1a1a2e" }}
            />
            <button
              onClick={runFitRecommendation}
              disabled={fitLoading}
              className="px-4 py-2 rounded-xl text-sm font-semibold flex-shrink-0"
              style={{
                background: fitLoading ? "#c4b5fd" : "linear-gradient(135deg, #7c3aed, #9333ea)",
                color: "#fff",
              }}
            >
              {fitLoading ? "분석 중…" : "추천 보기"}
            </button>
          </div>

          {fitError && (
            <p className="text-xs py-2 px-3 rounded-xl" style={{ color: "#dc2626", background: "#fef2f2", border: "1px solid #fecaca" }}>
              {fitError}
            </p>
          )}

          {fitResult && (
            <div className="rounded-xl p-4 space-y-3" style={{ background: "#faf8ff", border: "1px solid rgba(139,92,246,0.08)" }}>
              <p className="text-sm leading-relaxed" style={{ color: "#3d3960" }}>
                {fitResult.text}
              </p>

              {fitResult.size_distribution.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold" style={{ color: "#9d98b8" }}>구매 사이즈 비율</p>
                  {fitResult.size_distribution.map((d) => (
                    <div key={d.label}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs break-all pr-2" style={{ color: "#3d3960" }}>{d.label}</span>
                        <span className="text-xs font-bold flex-shrink-0" style={{ color: "#7c3aed" }}>{d.ratio}%</span>
                      </div>
                      <div className="rounded-full h-2" style={{ background: "#f0ecff" }}>
                        <div className="h-2 rounded-full" style={{ width: `${d.ratio}%`, background: "linear-gradient(to right, #6d28d9, #a78bfa)" }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {fitResult.fit_distribution.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold" style={{ color: "#9d98b8" }}>핏 만족도 비율</p>
                  {fitResult.fit_distribution.map((d) => (
                    <div key={d.label}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs break-all pr-2" style={{ color: "#3d3960" }}>{d.label}</span>
                        <span className="text-xs font-bold flex-shrink-0" style={{ color: "#059669" }}>{d.ratio}%</span>
                      </div>
                      <div className="rounded-full h-2" style={{ background: "#f0ecff" }}>
                        <div className="h-2 rounded-full" style={{ width: `${d.ratio}%`, background: "linear-gradient(to right, #059669, #34d399)" }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 분석 전 */}
        {!analysis && (
          <div
            className="rounded-2xl p-8 text-center space-y-4"
            style={{
              background: "rgba(255,255,255,0.8)",
              border: "1px solid rgba(139,92,246,0.1)",
              boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
            }}
          >
            <div
              className="w-12 h-12 mx-auto rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(124,58,237,0.08)", border: "1.5px solid rgba(124,58,237,0.2)" }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35M11 8v6M8 11h6" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold mb-1" style={{ color: "#1a1a2e" }}>
                리뷰 {reviews.length}개 분석 준비 완료
              </p>
              <p className="text-xs" style={{ color: "#7c6fa0" }}>
                13가지 속성별 감성 점수를 AI가 분석합니다
              </p>
            </div>
            {error && (
              <p className="text-xs py-2 px-3 rounded-xl" style={{ color: "#dc2626", background: "#fef2f2", border: "1px solid #fecaca" }}>
                {error}
              </p>
            )}
            {analyzing && progress && progress.total > 0 && (
              <div className="space-y-1.5">
                <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "#ede9fe" }}>
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, Math.round((progress.done / progress.total) * 100))}%`,
                      background: "linear-gradient(135deg, #7c3aed, #9333ea)",
                    }}
                  />
                </div>
                <p className="text-xs" style={{ color: "#7c6fa0" }}>
                  {progress.done} / {progress.total}개 문장 분석 중 (
                  {Math.min(100, Math.round((progress.done / progress.total) * 100))}%)
                </p>
              </div>
            )}
            <button
              onClick={runAnalysis}
              disabled={analyzing}
              className="px-8 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
              style={{
                background: analyzing ? "#c4b5fd" : "linear-gradient(135deg, #7c3aed, #9333ea)",
                color: "#fff",
                boxShadow: analyzing ? "none" : "0 4px 20px rgba(124,58,237,0.3)",
              }}
            >
              {analyzing ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  {progress && progress.total > 0 ? `분석 중… (${progress.done}/${progress.total})` : "분석 중…"}
                </span>
              ) : "AI 분석 시작"}
            </button>
          </div>
        )}

        {/* 분석 결과 */}
        {analysis && (
          <>
          <div
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.8)",
              border: "1px solid rgba(139,92,246,0.1)",
              boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
            }}
          >
            {/* 상단 헤더 + 상위 3점수 */}
            <div className="px-5 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(139,92,246,0.08)" }}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold" style={{ color: "#1a1a2e" }}>
                    속성별 감성 점수
                  </h3>
                  <p className="text-xs mt-0.5" style={{ color: "#9d98b8" }}>
                    리뷰 {analysis.review_count}개 기반
                  </p>
                </div>
                <button
                  onClick={runAnalysis}
                  disabled={analyzing}
                  className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all duration-150"
                  style={{
                    color: "#7c3aed",
                    background: "rgba(124,58,237,0.07)",
                    border: "1px solid rgba(124,58,237,0.2)",
                  }}
                >
                  {analyzing
                    ? progress && progress.total > 0
                      ? `분석 중… (${progress.done}/${progress.total})`
                      : "분석 중…"
                    : "재분석"}
                </button>
              </div>

              {analyzing && progress && progress.total > 0 && (
                <div className="mb-4 space-y-1.5">
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "#ede9fe" }}>
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(100, Math.round((progress.done / progress.total) * 100))}%`,
                        background: "linear-gradient(135deg, #7c3aed, #9333ea)",
                      }}
                    />
                  </div>
                  <p className="text-xs" style={{ color: "#7c6fa0" }}>
                    {progress.done} / {progress.total}개 문장 재분석 중
                  </p>
                </div>
              )}

              {weightedScore !== null && weightedGrade ? (
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: weightedGrade.bg, border: `1px solid ${weightedGrade.color}22` }}
                >
                  <div className="text-4xl font-extrabold" style={{ color: weightedGrade.color }}>
                    {weightedScore}
                  </div>
                  <div className="text-sm font-semibold mt-1" style={{ color: weightedGrade.color, opacity: 0.85 }}>
                    나의 종합 점수
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: "#9d98b8" }}>
                    관심 속성 가중 평균 · {scoredVisible.length}개 항목
                  </div>
                </div>
              ) : (
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "#f9f7ff", border: "1px solid rgba(139,92,246,0.1)" }}
                >
                  <p className="text-xs" style={{ color: "#9d98b8" }}>
                    관심 속성을 선택하면 종합 점수가 계산됩니다
                  </p>
                </div>
              )}
            </div>

            {error && (
              <div className="px-5 pt-3">
                <p className="text-xs py-2 px-3 rounded-xl" style={{ color: "#dc2626", background: "#fef2f2", border: "1px solid #fecaca" }}>
                  {error}
                </p>
              </div>
            )}

            {/* 탭 */}
            <div className="flex px-5 pt-3 gap-6" style={{ borderBottom: "1px solid rgba(139,92,246,0.08)" }}>
              {(["radar", "bars", "reviews"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className="pb-3 text-sm font-semibold transition-all duration-150 relative"
                  style={{ color: tab === t ? "#7c3aed" : "#9d98b8" }}
                >
                  {t === "radar" ? "레이더" : t === "bars" ? "막대" : "리뷰"}
                  {tab === t && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                      style={{ background: "linear-gradient(to right, #7c3aed, #a855f7)" }}
                    />
                  )}
                </button>
              ))}
            </div>

            {/* 탭 콘텐츠 */}
            <div className="p-5">
              {tab === "radar" && (
                <ScoreRadar
                  scores={analysis.scores}
                  averages={averages}
                  summaries={analysis.summaries}
                  visibleAspects={visibleAspects}
                />
              )}
              {tab === "bars" && (
                <ScoreBars
                  scores={analysis.scores}
                  averages={averages}
                  summaries={analysis.summaries}
                  visibleAspects={visibleAspects}
                />
              )}
              {tab === "reviews" && (
                <ul className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
                  {reviews.map((r) => (
                    <li
                      key={r.id}
                      className="rounded-xl p-4"
                      style={{ background: "#faf8ff", border: "1px solid rgba(139,92,246,0.08)" }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium" style={{ color: "#9d98b8" }}>
                          {r.reviewer ?? "익명"}
                        </span>
                        <div className="flex items-center gap-2">
                          {r.size_bought && (
                            <span
                              className="text-xs px-2 py-0.5 rounded-lg"
                              style={{ color: "#7c6fa0", background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.12)" }}
                            >
                              {r.size_bought}
                            </span>
                          )}
                          {r.rating !== null && (
                            <span className="text-xs" style={{ color: "#f59e0b" }}>
                              {"★".repeat(r.rating)}
                              <span style={{ color: "#e5e0f5" }}>{"★".repeat(5 - r.rating)}</span>
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm leading-relaxed" style={{ color: "#3d3960" }}>
                        {r.body}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* 의견 남기기 */}
          <div className="text-center pt-2 pb-4">
            <Link
              to="/feedback"
              state={{ productName: product.name, productUrl: window.location.origin + pathname }}
              className="inline-flex items-center gap-2 text-sm font-medium px-5 py-2.5 rounded-xl transition-all duration-150"
              style={{
                color: "#7c6fa0",
                background: "rgba(124,58,237,0.06)",
                border: "1px solid rgba(124,58,237,0.15)",
              }}
            >
              이 서비스 어떠세요? 의견 남기기
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
          </>
        )}
      </main>
    </div>
  );
}
