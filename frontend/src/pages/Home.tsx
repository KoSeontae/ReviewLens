import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Source } from "../api";

const SOURCES: { key: Source; label: string; hint: string }[] = [
  { key: "ably",    label: "에이블리", hint: "a-bly.com/goods/12345678" },
  { key: "musinsa", label: "무신사",   hint: "musinsa.com/products/1234567" },
  { key: "zigzag",  label: "지그재그", hint: "zigzag.kr/catalog/products/123456789" },
  { key: "hiver",   label: "하이버",   hint: "hiver.co.kr/products/123456789" },
];

const parseInput = (raw: string, fallback: Source): { source: Source; code: string } | null => {
  const s = raw.trim();
  const patterns: [RegExp, Source][] = [
    [/a-bly\.com\/goods\/(\d+)/, "ably"],
    [/musinsa\.com\/products\/(\d+)/, "musinsa"],
    [/zigzag\.kr\/catalog\/products\/(\d+)/, "zigzag"],
    [/hiver\.co\.kr\/products\/(\d+)/, "hiver"],
  ];
  for (const [re, src] of patterns) {
    const m = s.match(re);
    if (m) return { source: src, code: m[1] };
  }
  if (/^\d+$/.test(s)) return { source: fallback, code: s };
  return null;
};

export default function Home() {
  const [source, setSource] = useState<Source>("ably");
  const [productCode, setProductCode] = useState("");
  const [maxReviews, setMaxReviews] = useState<number | "">(50);
  const [reviewCountError, setReviewCountError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const hint = SOURCES.find((s) => s.key === source)?.hint ?? "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productCode.trim()) return;
    const parsed = parseInput(productCode, source);
    if (!parsed) {
      setError("올바른 상품 URL 또는 숫자 ID를 입력해주세요.");
      return;
    }
    if (maxReviews === "" || maxReviews < 1) {
      setReviewCountError("1개 이상 입력해주세요.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const product = await api.crawl(parsed.source, parsed.code, maxReviews);
      navigate(`/products/${product.source}/${product.product_code}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "리뷰를 불러오는 데 실패했습니다.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="relative min-h-screen flex flex-col items-center justify-center px-4 overflow-hidden"
      style={{ background: "linear-gradient(160deg, #f0edff 0%, #faf9ff 50%, #ede9fe 100%)" }}
    >
      {/* 배경 블롭 */}
      <div
        className="pointer-events-none absolute top-0 right-0"
        style={{
          width: 480,
          height: 480,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(167,139,250,0.18) 0%, transparent 70%)",
          transform: "translate(30%, -30%)",
        }}
      />
      <div
        className="pointer-events-none absolute bottom-0 left-0"
        style={{
          width: 360,
          height: 360,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(196,181,253,0.15) 0%, transparent 70%)",
          transform: "translate(-30%, 30%)",
        }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* 헤더 */}
        <div className="text-center mb-10">
          <span
            className="text-5xl font-extrabold tracking-tight"
            style={{
              background: "linear-gradient(135deg, #6d28d9 0%, #a855f7 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            ReviewLens
          </span>
          <p className="mt-3 text-sm" style={{ color: "#7c6fa0" }}>
            상품 URL을 붙여넣으면 리뷰를 분석해드립니다
          </p>
        </div>

        {/* 폼 카드 */}
        <form
          onSubmit={handleSubmit}
          className="rounded-3xl p-6 space-y-5"
          style={{
            background: "rgba(255,255,255,0.75)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(139,92,246,0.12)",
            boxShadow: "0 8px 40px rgba(109,40,217,0.08), 0 1px 3px rgba(109,40,217,0.06)",
          }}
        >
          {/* 쇼핑몰 선택 */}
          <div>
            <p className="text-xs font-semibold mb-2.5" style={{ color: "#6d28d9", letterSpacing: "0.06em" }}>
              쇼핑몰
            </p>
            <div className="grid grid-cols-4 gap-1.5">
              {SOURCES.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setSource(s.key)}
                  className="py-2 rounded-xl text-xs font-semibold transition-all duration-150"
                  style={
                    source === s.key
                      ? {
                          background: "linear-gradient(135deg, #7c3aed, #9333ea)",
                          color: "#fff",
                          boxShadow: "0 2px 12px rgba(124,58,237,0.3)",
                        }
                      : {
                          background: "rgba(109,40,217,0.05)",
                          border: "1px solid rgba(109,40,217,0.1)",
                          color: "#7c6fa0",
                        }
                  }
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* URL 입력 */}
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "#6d28d9", letterSpacing: "0.06em" }}>
              상품 URL 또는 ID
            </p>
            <input
              type="text"
              value={productCode}
              onChange={(e) => { setProductCode(e.target.value); setError(""); }}
              placeholder="URL 또는 숫자 ID 붙여넣기"
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all duration-200"
              style={{
                background: "#faf8ff",
                border: error ? "1.5px solid #f87171" : "1.5px solid rgba(109,40,217,0.15)",
                color: "#1a1a2e",
                boxShadow: "inset 0 1px 3px rgba(109,40,217,0.04)",
              }}
              onFocus={(e) => {
                if (!error) e.target.style.border = "1.5px solid rgba(124,58,237,0.5)";
                e.target.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.1)";
              }}
              onBlur={(e) => {
                e.target.style.border = error ? "1.5px solid #f87171" : "1.5px solid rgba(109,40,217,0.15)";
                e.target.style.boxShadow = "inset 0 1px 3px rgba(109,40,217,0.04)";
              }}
            />
            <p className="mt-2 text-xs flex items-center gap-1" style={{ color: "#bdb8d4" }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
              </svg>
              예) <span style={{ color: "#a78bfa" }}>{hint}</span>
            </p>
          </div>

          {/* 리뷰 수 입력 */}
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "#6d28d9", letterSpacing: "0.06em" }}>
              수집 리뷰 수
            </p>
            <input
              type="number"
              min={1}
              value={maxReviews}
              onChange={(e) => {
                const val = e.target.value;
                if (val === "") {
                  setMaxReviews("");
                  setReviewCountError("");
                } else {
                  const num = Number(val);
                  setMaxReviews(num);
                  setReviewCountError(num < 1 ? "1개 이상 입력해주세요." : "");
                }
              }}
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all duration-200"
              style={{
                background: "#faf8ff",
                border: reviewCountError ? "1.5px solid #f87171" : "1.5px solid rgba(109,40,217,0.15)",
                color: "#1a1a2e",
                boxShadow: "inset 0 1px 3px rgba(109,40,217,0.04)",
              }}
              onFocus={(e) => {
                e.target.style.border = "1.5px solid rgba(124,58,237,0.5)";
                e.target.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.1)";
              }}
              onBlur={(e) => {
                e.target.style.border = reviewCountError ? "1.5px solid #f87171" : "1.5px solid rgba(109,40,217,0.15)";
                e.target.style.boxShadow = "inset 0 1px 3px rgba(109,40,217,0.04)";
              }}
            />
            {reviewCountError ? (
              <p className="mt-2 text-xs flex items-center gap-1" style={{ color: "#dc2626" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
                </svg>
                {reviewCountError}
              </p>
            ) : (
            <p className="mt-2 text-xs flex items-center gap-1" style={{ color: "#bdb8d4" }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
              </svg>
              50~150개를 권장합니다. 많을수록 분석이 오래 걸려요.
            </p>
            )}
          </div>

          {/* 에러 */}
          {error && (
            <p
              className="text-xs text-center py-2 px-3 rounded-xl"
              style={{ color: "#dc2626", background: "#fef2f2", border: "1px solid #fecaca" }}
            >
              {error}
            </p>
          )}

          {/* 버튼 */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-200"
            style={{
              background: loading
                ? "#c4b5fd"
                : "linear-gradient(135deg, #7c3aed 0%, #9333ea 100%)",
              color: "#fff",
              boxShadow: loading ? "none" : "0 4px 20px rgba(124,58,237,0.35)",
            }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                리뷰 수집 중…
              </span>
            ) : (
              "리뷰 수집 및 분석 시작"
            )}
          </button>
        </form>

        <p className="text-center mt-5 text-xs" style={{ color: "#c4b5fd" }}>
          에이블리 · 무신사 · 지그재그 · 하이버 지원
        </p>
      </div>
    </div>
  );
}
