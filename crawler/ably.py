"""
에이블리(Ably) 상품 리뷰 크롤러.

에이블리 앱의 내부 API를 통해 리뷰 JSON을 수집합니다.
요청 간 딜레이를 준수하며, 한 번에 20개씩 페이지네이션합니다.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class Review:
    product_id: str
    product_name: str
    reviewer: str
    rating: int
    body: str
    size_bought: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    created_at: str


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    ),
    "Accept": "application/json",
    "Referer": "https://m.a-bly.com/",
}

_BASE_URL = "https://api.a-bly.com"


async def _random_delay() -> None:
    await asyncio.sleep(random.uniform(1.0, 2.5))


async def _fetch_product_name(client: httpx.AsyncClient, product_id: str) -> str:
    try:
        resp = await client.get(f"{_BASE_URL}/goods/{product_id}", headers=_HEADERS, timeout=10)
        data = resp.json()
        return data.get("goods", {}).get("name", product_id)
    except Exception:
        return product_id


async def _fetch_review_page(
    client: httpx.AsyncClient,
    product_id: str,
    page: int,
) -> list[dict]:
    params = {"goods_no": product_id, "page": page, "per_page": 20}
    try:
        resp = await client.get(
            f"{_BASE_URL}/goods/reviews",
            params=params,
            headers=_HEADERS,
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
        product_id: 에이블리 상품 번호
        max_reviews: 최대 수집 리뷰 수
    Returns:
        Review 객체 목록
    """
    reviews: list[Review] = []

    async with httpx.AsyncClient() as client:
        product_name = await _fetch_product_name(client, product_id)

        page = 1
        while len(reviews) < max_reviews:
            items = await _fetch_review_page(client, product_id, page)
            if not items:
                break

            for item in items:
                if len(reviews) >= max_reviews:
                    break

                body = item.get("content", "").strip()
                if not body:
                    continue

                user_info = item.get("user_info", {})
                option_info = item.get("option_info", {})

                reviews.append(Review(
                    product_id=product_id,
                    product_name=product_name,
                    reviewer=user_info.get("nickname", "익명"),
                    rating=int(item.get("score", 0)),
                    body=body,
                    size_bought=option_info.get("size"),
                    height=str(user_info.get("height")) if user_info.get("height") else None,
                    weight=str(user_info.get("weight")) if user_info.get("weight") else None,
                    created_at=item.get("created_at", ""),
                ))

            page += 1
            await _random_delay()

    return reviews


if __name__ == "__main__":
    import json

    async def main():
        results = await crawl_product_reviews("12345678", max_reviews=30)
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))

    asyncio.run(main())
