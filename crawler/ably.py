"""
에이블리(Ably) 상품 리뷰 크롤러.

webview API를 통해 리뷰 JSON을 수집합니다.
요청 간 딜레이를 준수하며, 한 번에 20개씩 페이지네이션합니다.
"""

import asyncio
import os
import random
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Review:
    product_id: str
    product_name: str
    image_url: Optional[str]
    reviewer: str
    rating: int
    body: str
    size_bought: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    created_at: str


def _make_headers() -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://m.a-bly.com",
        "Referer": "https://m.a-bly.com/",
        "x-device-type": "PCWeb",
        "x-web-type": "Web",
        "x-app-version": "0.1.0",
        "x-device-id": str(uuid.uuid4()),
    }
    token = os.getenv("ABLY_ANONYMOUS_TOKEN", "")
    if token:
        headers["x-anonymous-token"] = token
    return headers


async def _random_delay() -> None:
    await asyncio.sleep(random.uniform(1.0, 2.5))


async def _fetch_product_info(client: httpx.AsyncClient, product_id: str) -> tuple[str, Optional[str]]:
    """상품명과 대표 이미지 URL 반환."""
    try:
        resp = await client.get(
            f"https://api.a-bly.com/api/v2/goods/{product_id}/",
            headers=_make_headers(),
            timeout=10,
        )
        data = resp.json()
        goods = data.get("goods", {})
        name = goods.get("name", product_id)
        image_url = goods.get("image") or (goods.get("cover_images") or [None])[0]
        return name, image_url
    except Exception:
        return product_id, None


async def _fetch_review_page(
    client: httpx.AsyncClient,
    product_id: str,
    page: int,
) -> list[dict]:
    params = {"page": page, "per_page": 20}
    try:
        resp = await client.get(
            f"https://api.a-bly.com/webview/goods/{product_id}/reviews/",
            params=params,
            headers=_make_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("reviews", [])
    except Exception:
        return []


async def crawl_product_reviews(
    product_id: str,
    max_reviews: int = 100,
) -> list[Review]:
    """
    에이블리 상품 리뷰를 수집합니다.

    Args:
        product_id: 에이블리 상품 번호 (URL의 숫자 부분)
        max_reviews: 최대 수집 리뷰 수
    Returns:
        Review 객체 목록
    """
    reviews: list[Review] = []

    async with httpx.AsyncClient() as client:
        product_name, image_url = await _fetch_product_info(client, product_id)

        page = 1
        while len(reviews) < max_reviews:
            items = await _fetch_review_page(client, product_id, page)
            if not items:
                break

            for item in items:
                if len(reviews) >= max_reviews:
                    break

                body = item.get("contents", "").strip()
                if not body:
                    continue

                options = item.get("goods_option", [])
                size_bought = options[1] if len(options) >= 2 else (options[0] if options else None)

                reviews.append(Review(
                    product_id=product_id,
                    product_name=item.get("goods_name", product_name),
                    image_url=image_url,
                    reviewer=item.get("writer", "익명"),
                    rating=int(item.get("eval", 0)),
                    body=body,
                    size_bought=size_bought,
                    height=str(item["height"]) if item.get("height") else None,
                    weight=str(item["weight"]) if item.get("weight") else None,
                    created_at=item.get("created_at", ""),
                ))

            page += 1
            await _random_delay()

    return reviews


@dataclass
class FitReview:
    height: Optional[int]
    weight: Optional[int]
    size_bought: Optional[str]
    fit_raw_label: Optional[int]  # size_rate (1~5 스케일)


async def crawl_fit_reviews(
    product_id: str,
    max_reviews: int = 200,
) -> list[FitReview]:
    """체형 유사 추천용 핏 데이터(키/몸무게/구매사이즈/사이즈 평가)를 수집합니다."""
    fit_reviews: list[FitReview] = []

    async with httpx.AsyncClient() as client:
        page = 1
        while len(fit_reviews) < max_reviews:
            items = await _fetch_review_page(client, product_id, page)
            if not items:
                break

            for item in items:
                if len(fit_reviews) >= max_reviews:
                    break

                options = item.get("goods_option", [])
                size_bought = options[1] if len(options) >= 2 else (options[0] if options else None)

                fit_reviews.append(FitReview(
                    height=int(item["height"]) if item.get("height") else None,
                    weight=int(item["weight"]) if item.get("weight") else None,
                    size_bought=size_bought,
                    fit_raw_label=item.get("size_rate"),
                ))

            page += 1
            await _random_delay()

    return fit_reviews


if __name__ == "__main__":
    import json

    async def main():
        results = await crawl_product_reviews("45314288", max_reviews=30)
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))

    asyncio.run(main())
