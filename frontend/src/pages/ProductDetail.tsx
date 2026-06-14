import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";
import type { Product, AnalysisResult, Review, Source } from "../api";
import ScoreRadar from "../components/ScoreRadar";
import ScoreBars from "../components/ScoreBars";

type Tab = "radar" | "bars" | "reviews";

const SOURCE_LABELS: Record<Source, string> = {
  ably: "에이블리",
  musinsa: "무신사",
};

export default function ProductDetail() {
  const { source, code } = useParams<{ source: Source; code: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [tab, setTab] = useState<Tab>("radar");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!source || !code) return;
    api.getProduct(source, code).then(setProduct).catch(() => setError("상품 정보를 불러올 수 없습니다."));
    api.getAnalysis(source, code).then(setAnalysis).catch(() => {});
    api.getReviews(source, code).then(setReviews).catch(() => {});
  }, [source, code]);

  const runAnalysis = async () => {
    if (!source || !code) return;
    setAnalyzing(true);
    setError("");
    try {
      const result = await api.analyze(source, code);
      const updatedReviews = await api.getReviews(source, code);
      setAnalysis(result);
      setReviews(updatedReviews);
    } catch {
      setError("분석 중 오류가 발생했습니다.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        {error || "로딩 중..."}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm px-6 py-4 flex items-center gap-4">
        <Link to="/" className="text-indigo-600 hover:underline text-sm">
          ← 홈
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full font-medium">
              {SOURCE_LABELS[product.source as Source]}
            </span>
            <h2 className="text-lg font-bold text-gray-800 leading-tight">{product.name}</h2>
          </div>
          <p className="text-xs text-gray-400">ID: {product.product_code}</p>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {!analysis && (
          <div className="bg-white rounded-2xl shadow p-6 text-center space-y-3">
            <p className="text-gray-600">
              수집된 리뷰 <strong>{reviews.length}개</strong>에 대한 ABSA 분석을 실행합니다.
            </p>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              onClick={runAnalysis}
              disabled={analyzing}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-semibold transition"
            >
              {analyzing ? "분석 중..." : "AI 분석 시작"}
            </button>
          </div>
        )}

        {analysis && (
          <div className="bg-white rounded-2xl shadow p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-gray-800">속성별 감성 점수</h3>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">리뷰 {analysis.review_count}개 기반</span>
                <button
                  onClick={runAnalysis}
                  disabled={analyzing}
                  className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 border border-indigo-300 rounded px-2 py-1 transition"
                >
                  {analyzing ? "분석 중..." : "재분석"}
                </button>
              </div>
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <div className="flex gap-2 border-b pb-2">
              {(["radar", "bars", "reviews"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`text-sm px-3 py-1 rounded-full transition ${
                    tab === t
                      ? "bg-indigo-600 text-white"
                      : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  {t === "radar" ? "레이더" : t === "bars" ? "막대" : "리뷰"}
                </button>
              ))}
            </div>

            {tab === "radar" && <ScoreRadar scores={analysis.scores} />}
            {tab === "bars" && <ScoreBars scores={analysis.scores} />}
            {tab === "reviews" && (
              <ul className="space-y-3 max-h-96 overflow-y-auto">
                {reviews.map((r) => (
                  <li key={r.id} className="border rounded-lg p-3 text-sm">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>{r.reviewer ?? "익명"}</span>
                      <span>{"★".repeat(r.rating ?? 0)}</span>
                    </div>
                    <p className="text-gray-700 leading-relaxed">{r.body}</p>
                    {r.size_bought && (
                      <p className="text-xs text-gray-400 mt-1">구매 옵션: {r.size_bought}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
