import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export type Source = "ably" | "musinsa" | "zigzag";

export interface Product {
  id: number;
  source: Source;
  product_code: string;
  name: string;
  brand: string | null;
  image_url: string | null;
  created_at: string;
}

export interface Review {
  id: number;
  reviewer: string | null;
  rating: number | null;
  body: string;
  size_bought: string | null;
  height: string | null;
  weight: string | null;
  crawled_at: string;
}

export interface AnalysisResult {
  id: number;
  product_id: number;
  review_count: number;
  scores: Record<string, number>;
  summaries: Record<string, string> | null;
  analyzed_at: string;
}

export const ALL_ASPECTS: { key: string; label: string }[] = [
  { key: "fit", label: "핏" },
  { key: "material", label: "소재" },
  { key: "finish", label: "마감" },
  { key: "size", label: "사이즈" },
  { key: "price", label: "가격" },
  { key: "color", label: "색상" },
  { key: "design", label: "디자인" },
  { key: "comfort", label: "착용감" },
  { key: "delivery", label: "배송" },
  { key: "care", label: "관리" },
  { key: "sheerness", label: "비침" },
  { key: "stretch", label: "신축성" },
  { key: "season", label: "계절감" },
];

export const api = {
  getAverages: () => client.get<Record<string, number>>("/products/averages").then((r) => r.data),
  listProducts: () => client.get<Product[]>("/products/").then((r) => r.data),
  getProduct: (source: Source, code: string) =>
    client.get<Product>(`/products/${source}/${code}`).then((r) => r.data),
  getReviews: (source: Source, code: string) =>
    client.get<Review[]>(`/products/${source}/${code}/reviews`).then((r) => r.data),
  getAnalysis: (source: Source, code: string) =>
    client.get<AnalysisResult>(`/products/${source}/${code}/analysis`).then((r) => r.data),
  crawl: (source: Source, product_code: string, max_reviews = 100) =>
    client.post<Product>("/products/crawl", { source, product_code, max_reviews }).then((r) => r.data),
  analyze: (source: Source, product_code: string) =>
    client.post<AnalysisResult>("/products/analyze", { source, product_code }).then((r) => r.data),
};
