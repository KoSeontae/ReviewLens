import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Home() {
  const [productId, setProductId] = useState("");
  const [maxReviews, setMaxReviews] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId.trim()) return;
    setError("");
    setLoading(true);
    try {
      const product = await api.crawl(productId.trim(), maxReviews);
      navigate(`/products/${product.product_code}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "크롤링 중 오류가 발생했습니다.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center px-4">
      <div className="max-w-lg w-full">
        <h1 className="text-4xl font-bold text-indigo-700 mb-2 text-center">ReviewLens</h1>
        <p className="text-gray-500 text-center mb-8">
          에이블리 상품 번호를 입력하면 리뷰를 분석해드립니다
        </p>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              에이블리 상품 ID
            </label>
            <input
              type="text"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              placeholder="예) 12345678"
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
          상품 URL에서 숫자 ID를 확인하세요 · 예) a-bly.com/goods/<strong>12345678</strong>
        </p>
      </div>
    </div>
  );
}
