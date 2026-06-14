import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Source } from "../api";

const SOURCE_LABELS: Record<Source, string> = {
  ably: "에이블리",
  musinsa: "무신사",
  zigzag: "지그재그",
};

export default function Home() {
  const [source, setSource] = useState<Source>("ably");
  const [productCode, setProductCode] = useState("");
  const [maxReviews, setMaxReviews] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productCode.trim()) return;
    setError("");
    setLoading(true);
    try {
      const product = await api.crawl(source, productCode.trim(), maxReviews);
      navigate(`/products/${product.source}/${product.product_code}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "크롤링 중 오류가 발생했습니다.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const placeholder =
    source === "ably" ? "예) 45314288" :
    source === "musinsa" ? "예) 4992830" :
    "예) 114747784";
  const urlHint =
    source === "ably" ? "a-bly.com/goods/45314288" :
    source === "musinsa" ? "musinsa.com/products/4992830" :
    "zigzag.kr/catalog/products/114747784?tab=review";

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center px-4">
      <div className="max-w-lg w-full">
        <h1 className="text-4xl font-bold text-indigo-700 mb-2 text-center">ReviewLens</h1>
        <p className="text-gray-500 text-center mb-8">
          쇼핑몰 상품 번호를 입력하면 리뷰를 분석해드립니다
        </p>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          {/* 쇼핑몰 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">쇼핑몰</label>
            <div className="flex gap-2">
              {(Object.keys(SOURCE_LABELS) as Source[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSource(s)}
                  className={`flex-1 py-2 rounded-lg text-sm font-semibold border transition ${
                    source === s
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "text-gray-500 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {SOURCE_LABELS[s]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {SOURCE_LABELS[source]} 상품 ID
            </label>
            <input
              type="text"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              placeholder={placeholder}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              수집할 리뷰 수 (최대 200)
            </label>
            <input
              type="number"
              value={maxReviews}
              min={10}
              max={200}
              onChange={(e) => setMaxReviews(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
          >
            {loading ? "수집 중..." : "리뷰 수집 및 분석 시작"}
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-4">
          상품 URL에서 숫자 ID를 확인하세요 · 예) <strong>{urlHint}</strong>
        </p>
      </div>
    </div>
  );
}
