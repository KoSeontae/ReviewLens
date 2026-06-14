"""
무신사(Musinsa) 상품 리뷰 크롤러.

내부 REST API를 통해 리뷰 JSON을 수집합니다.
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
    image_url: Optional[str]
    reviewer: str
    rating: int
    body: str
    size_bought: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    created_at: str


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.musinsa.com/",
}

_BASE_URL = "https://api.musinsa.com/api2/review/v1/view/list"


async def _random_delay() -> None:
    await asyncio.sleep(random.uniform(1.0, 2.5))


async def _fetch_review_page(
    client: httpx.AsyncClient,
    product_id: str,
    page: int,
    size: int = 20,
) -> tuple[list[dict], int]:
    """리뷰 페이지 fetch. (리뷰 목록, 전체 수) 반환."""
    params = {"goodsNo": product_id, "page": page, "size": size}
    try:
        resp = await client.get(_BASE_URL, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return data.get("list", []), int(data.get("total", 0))
    except Exception:
        return [], 0


async def crawl_product_reviews(
    product_id: str,
    max_reviews: int = 100,
) -> list[Review]:
    """
    무신사 상품 리뷰를 수집합니다.

    Args:
        product_id: 무신사 상품 번호 (URL의 숫자 부분)
        max_reviews: 최대 수집 리뷰 수
    Returns:
        Review 객체 목록
    """
    reviews: list[Review] = []

    async with httpx.AsyncClient() as client:
        page = 1
        product_name = product_id
        image_url: Optional[str] = None

        while len(reviews) < max_reviews:
            items, total = await _fetch_review_page(client, product_id, page)
            if not items:
                break

            for item in items:
                if len(reviews) >= max_reviews:
                    break

                body = (item.get("content") or "").strip()
                if not body:
                    continue

                goods = item.get("goods", {})
                if page == 1 and not reviews:
                    product_name = goods.get("goodsName", product_id)
                    img_path = goods.get("goodsImageFile", "")
                    img_path_hq = img_path.replace("_100.", "_500.") if img_path else ""
                    image_url = f"https://image.musinsa.com{img_path_hq}" if img_path_hq else None

                profile = item.get("userProfileInfo") or {}
                height = profile.get("userHeight")
                weight = profile.get("userWeight")

                reviews.append(Review(
                    product_id=product_id,
                    product_name=product_name,
                    image_url=image_url,
                    reviewer=profile.get("userNickName", "익명"),
                    rating=int(item.get("grade") or 0),
                    body=body,
                    size_bought=item.get("goodsOption"),
                    height=str(height) if height else None,
                    weight=str(weight) if weight else None,
                    created_at=item.get("createDate", ""),
                ))

            if len(reviews) >= total:
                break

            page += 1
            await _random_delay()

    return reviews


if __name__ == "__main__":
    import json

    async def main():
        results = await crawl_product_reviews("4992830", max_reviews=10)
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))

    asyncio.run(main())
