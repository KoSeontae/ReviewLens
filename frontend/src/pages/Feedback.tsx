import { useState } from "react";
import { useLocation, Link, useNavigate } from "react-router-dom";
import { submitFeedback } from "../utils/tracking";

type LocationState = { productName?: string; productUrl?: string };

const CARD_STYLE: React.CSSProperties = {
  background: "rgba(255,255,255,0.8)",
  border: "1px solid rgba(139,92,246,0.1)",
  boxShadow: "0 2px 16px rgba(109,40,217,0.06)",
};

const INPUT_STYLE: React.CSSProperties = {
  background: "#f9f7ff",
  border: "1.5px solid rgba(139,92,246,0.2)",
  color: "#1a1a2e",
  outline: "none",
  width: "100%",
  borderRadius: "0.75rem",
  padding: "0.75rem 1rem",
  fontSize: "0.875rem",
};

export default function Feedback() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = (location.state ?? {}) as LocationState;

  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) {
      setError("의견을 입력해주세요.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await submitFeedback(email.trim(), message.trim(), state.productUrl ?? "");
      setSubmitted(true);
    } catch {
      setError("전송 중 오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(160deg, #f0edff 0%, #faf9ff 60%, #ede9fe 100%)" }}
    >
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
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-sm font-medium transition-colors duration-150"
          style={{ color: "#7c3aed" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          뒤로
        </button>
        <span className="text-sm font-semibold" style={{ color: "#1a1a2e" }}>의견 남기기</span>
      </header>

      <main className="max-w-lg mx-auto px-4 py-10 space-y-4">
        {/* 분석 상품 표시 */}
        {state.productName && (
          <div className="rounded-2xl px-5 py-4" style={CARD_STYLE}>
            <p className="text-xs mb-0.5" style={{ color: "#9d98b8" }}>분석한 상품</p>
            <p className="text-sm font-semibold truncate" style={{ color: "#1a1a2e" }}>
              {state.productName}
            </p>
          </div>
        )}

        {submitted ? (
          /* ── 제출 완료 ── */
          <div className="rounded-2xl p-8 text-center space-y-5" style={CARD_STYLE}>
            <div
              className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(5,150,105,0.08)", border: "1.5px solid rgba(5,150,105,0.2)" }}
            >
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div>
              <p className="text-base font-bold" style={{ color: "#1a1a2e" }}>의견이 전달되었어요!</p>
              <p className="text-sm mt-1.5 leading-relaxed" style={{ color: "#7c6fa0" }}>
                소중한 피드백 감사합니다.<br />서비스 개선에 반영할게요.
              </p>
            </div>
            <div className="flex flex-col gap-2 pt-1">
              <button
                onClick={() => navigate(-2)}
                className="w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
                style={{
                  background: "linear-gradient(135deg, #7c3aed, #9333ea)",
                  color: "#fff",
                  boxShadow: "0 4px 20px rgba(124,58,237,0.3)",
                }}
              >
                결과로 돌아가기
              </button>
              <Link
                to="/app"
                className="w-full py-2.5 rounded-xl text-sm font-semibold text-center block"
                style={{
                  background: "rgba(124,58,237,0.07)",
                  color: "#7c3aed",
                  border: "1px solid rgba(124,58,237,0.2)",
                }}
              >
                새 상품 분석하기
              </Link>
            </div>
          </div>
        ) : (
          /* ── 피드백 폼 ── */
          <form onSubmit={handleSubmit} className="rounded-2xl p-6 space-y-5" style={CARD_STYLE}>
            <div>
              <p className="text-base font-bold" style={{ color: "#1a1a2e" }}>어떠셨나요?</p>
              <p className="text-xs mt-1" style={{ color: "#9d98b8" }}>
                서비스 개선을 위한 의견을 자유롭게 남겨주세요.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold block" style={{ color: "#6d28d9" }}>
                의견 <span style={{ color: "#dc2626" }}>*</span>
              </label>
              <textarea
                value={message}
                onChange={(e) => { setMessage(e.target.value); setError(""); }}
                placeholder="분석 결과가 도움이 됐나요? 불편한 점이나 개선 사항이 있다면 알려주세요."
                rows={5}
                style={{ ...INPUT_STYLE, resize: "none" }}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold block" style={{ color: "#6d28d9" }}>
                이메일{" "}
                <span style={{ color: "#bdb8d4", fontWeight: 400 }}>(선택 · 답변 받고 싶을 때)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@email.com"
                style={INPUT_STYLE}
              />
            </div>

            {error && (
              <p
                className="text-xs py-2 px-3 rounded-xl"
                style={{ color: "#dc2626", background: "#fef2f2", border: "1px solid #fecaca" }}
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
              style={{
                background: submitting ? "#c4b5fd" : "linear-gradient(135deg, #7c3aed, #9333ea)",
                color: "#fff",
                boxShadow: submitting ? "none" : "0 4px 20px rgba(124,58,237,0.3)",
              }}
            >
              {submitting ? "전송 중…" : "의견 보내기"}
            </button>
          </form>
        )}
      </main>
    </div>
  );
}
