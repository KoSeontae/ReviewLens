"""
하이버(Hiver) 상품 리뷰 크롤러.

Brandi 기반 REST API를 통해 offset 기반 페이지네이션으로 리뷰를 수집합니다.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup

_REVIEW_API = "https://hiver-api.brandi.biz/v2/web/products"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.hiver.co.kr",
    "Referer": "https://www.hiver.co.kr/",
}


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


async def _fetch_product_info(client: httpx.AsyncClient, product_id: str) -> tuple[str, Optional[str]]:
    """상품 페이지 og 태그에서 상품명과 썸네일 URL을 가져옵니다."""
    try:
        resp = await client.get(
            f"https://www.hiver.co.kr/products/{product_id}",
            headers={**_HEADERS, "Accept": "text/html"},
            timeout=15,
            follow_redirects=True,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        raw_title = og_title.get("content", product_id) if og_title else product_id
        # "상품명 | 가격 | 하이버" 형식에서 상품명만 추출
        name = raw_title.split(" | ")[0].strip()
        image_url = og_image.get("content") if og_image else None
        return name, image_url
    except Exception:
        return product_id, None


async def _fetch_review_page(
    client: httpx.AsyncClient,
    product_id: str,
    offset: int,
    is_first: bool,
) -> dict:
    params = {
        "version": "2605",
        "is-first": "true" if is_first else "false",
        "has-top-photo-reviews": "true" if is_first else "false",
        "offset": offset,
        "limit": 20,
        "service-type": "hiver",
    }
    try:
        resp = await client.get(
            f"{_REVIEW_API}/{product_id}/reviews",
            params=params,
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _parse_item(item: dict, product_id: str, product_name: str, image_url: Optional[str]) -> Optional[Review]:
    body = (item.get("text") or "").strip()
    if not body:
        return None

    user = item.get("user") or {}
    product = item.get("product") or {}
    evaluation = item.get("evaluation") or {}

    raw_height = user.get("height") or 0
    raw_weight = user.get("weight") or 0

    return Review(
        product_id=product_id,
        product_name=product_name,
        image_url=image_url,
        reviewer=user.get("name", "익명"),
        rating=int(evaluation.get("satisfaction") or 0),
        body=body,
        size_bought=product.get("option_name") or None,
        height=f"{raw_height}cm" if raw_height > 0 else None,
        weight=f"{raw_weight}kg" if raw_weight > 0 else None,
        created_at=str(item.get("created_time", "")),
    )


async def crawl_product_reviews(
    product_id: str,
    max_reviews: int = 100,
) -> list[Review]:
    reviews: list[Review] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient() as client:
        product_name, image_url = await _fetch_product_info(client, product_id)

        offset = 0
        is_first = True

        page_size = 20
        while len(reviews) < max_reviews:
            resp_json = await _fetch_review_page(client, product_id, offset, is_first)
            if not resp_json:
                break

            raw = resp_json.get("data", {})

            items: list[dict] = []
            page_reviews: list[dict] = []  # 페이지 종료 여부 판단용 (top_photo 제외)
            if isinstance(raw, list):
                items.extend(raw)
                page_reviews = raw
            else:
                if is_first:
                    items.extend(raw.get("top_photo_reviews") or [])
                page_reviews = raw.get("reviews") or []
                items.extend(page_reviews)

            if not items:
                break

            for item in items:
                if len(reviews) >= max_reviews:
                    break
                review_id = str(item.get("id", ""))
                if review_id in seen_ids:
                    continue
                seen_ids.add(review_id)
                review = _parse_item(item, product_id, product_name, image_url)
                if review:
                    reviews.append(review)

            # 이번 페이지 리뷰가 page_size 미만이면 마지막 페이지
            if len(page_reviews) < page_size:
                break

            offset += page_size
            is_first = False
            await asyncio.sleep(random.uniform(1.0, 2.0))

    return reviews


if __name__ == "__main__":
    import json

    async def main():
        results = await crawl_product_reviews("175466788", max_reviews=10)
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))

    asyncio.run(main())
