import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export interface Product {
  id: number;
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
  analyzed_at: string;
}

export const api = {
  listProducts: () => client.get<Product[]>("/products/").then((r) => r.data),
  getProduct: (code: string) => client.get<Product>(`/products/${code}`).then((r) => r.data),
  getReviews: (code: string) => client.get<Review[]>(`/products/${code}/reviews`).then((r) => r.data),
  getAnalysis: (code: string) => client.get<AnalysisResult>(`/products/${code}/analysis`).then((r) => r.data),
  crawl: (product_code: string, max_reviews = 100) =>
    client.post<Product>("/products/crawl", { product_code, max_reviews }).then((r) => r.data),
  analyze: (product_code: string) =>
    client.post<AnalysisResult>("/products/analyze", { product_code }).then((r) => r.data),
};
