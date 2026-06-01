import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export interface Product {
  id: number;
  musinsa_id: string;
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
  analyzed_at: string;
}

export const api = {
  listProducts: () => client.get<Product[]>("/products/").then((r) => r.data),
  getProduct: (id: string) => client.get<Product>(`/products/${id}`).then((r) => r.data),
  getReviews: (id: string) => client.get<Review[]>(`/products/${id}/reviews`).then((r) => r.data),
  getAnalysis: (id: string) => client.get<AnalysisResult>(`/products/${id}/analysis`).then((r) => r.data),
  crawl: (ably_id: string, max_reviews = 100) =>
    client.post<Product>("/products/crawl", { musinsa_id: ably_id, max_reviews }).then((r) => r.data),
  analyze: (ably_id: string) =>
    client.post<AnalysisResult>("/products/analyze", { musinsa_id: ably_id }).then((r) => r.data),
};
