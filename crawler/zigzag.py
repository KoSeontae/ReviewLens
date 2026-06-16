"""
지그재그(Zigzag) 상품 리뷰 크롤러.

GraphQL 배치 API를 통해 커서 기반 페이지네이션으로 리뷰를 수집합니다.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Optional

import httpx

_GQL_URL = "https://api.zigzag.kr/api/2/graphql/batch/GetReviewSearchList"

_QUERY = """
query GetReviewSearchList($input: UxReviewSearchListInput!) {
  ux_review_search_list(input: $input) {
    total_count
    has_next
    end_cursor
    component_list {
      type
      ... on UxReviewListItem {
        review {
          id
          contents
          rating
          reviewer {
            body_text
            profile {
              nickname
            }
          }
          product_info {
            name
            option_detail_list {
              name
              value
            }
          }
        }
      }
    }
  }
}
"""

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Origin": "https://zigzag.kr",
    "Referer": "https://zigzag.kr/",
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


def _parse_body_text(body_text: str) -> tuple[Optional[str], Optional[str]]:
    """'168cm,48kg,상의 55' 형식에서 키/몸무게 파싱."""
    if not body_text:
        return None, None
    height, weight = None, None
    for part in body_text.split(","):
        part = part.strip()
        if "cm" in part:
            height = part
        elif "kg" in part:
            weight = part
    return height, weight


async def _fetch_page(
    client: httpx.AsyncClient,
    product_id: str,
    cursor: Optional[str],
) -> tuple[list[dict], bool, Optional[str]]:
    """한 페이지 fetch. (리뷰 목록, has_next, end_cursor) 반환."""
    variables: dict = {
        "input": {
            "product_id": product_id,
            "order": "SCORE_DESC",
            "body_filter": {
                "my_body_filter_checked": False,
                "similar_body_filter_checked": False,
                "option_list": [],
                "has_my_body_reviews": None,
            },
            "option_detail_list": [],
            "topic_list": [],
            "type_list": [],
            "cursor": {"end_cursor": cursor, "limit_count": 20},
        }
    }

    payload = [{"operationName": "GetReviewSearchList", "query": _QUERY, "variables": variables}]

    try:
        resp = await client.post(_GQL_URL, json=payload, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        data = body[0].get("data", {}).get("ux_review_search_list", {})
        items = data.get("component_list", [])
        has_next = data.get("has_next", False)
        end_cursor = data.get("end_cursor")
        return items, has_next, end_cursor
    except Exception:
        return [], False, None


async def _fetch_product_image(client: httpx.AsyncClient, product_id: str) -> Optional[str]:
    """상품 페이지 og:image 태그에서 썸네일 URL을 가져옵니다."""
    try:
        from bs4 import BeautifulSoup
        headers = {**_HEADERS, "Accept": "text/html"}
        resp = await client.get(
            f"https://zigzag.kr/catalog/products/{product_id}",
            headers=headers,
            timeout=15,
            follow_redirects=True,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        og = soup.find("meta", property="og:image")
        return og.get("content") if og else None
    except Exception:
        return None


async def crawl_product_reviews(
    product_id: str,
    max_reviews: int = 100,
) -> list[Review]:
    reviews: list[Review] = []
    cursor: Optional[str] = None
    product_name = product_id
    image_url: Optional[str] = None

    async with httpx.AsyncClient() as client:
        image_url = await _fetch_product_image(client, product_id)

        while len(reviews) < max_reviews:
            items, has_next, cursor = await _fetch_page(client, product_id, cursor)
            if not items:
                break

            for item in items:
                if item.get("type") != "REVIEW_SEARCH_ITEM":
                    continue
                review = item.get("review")
                if not review:
                    continue

                body = (review.get("contents") or "").strip()
                if not body:
                    continue

                if not reviews:
                    info = review.get("product_info") or {}
                    product_name = info.get("name", product_id)

                nickname = (
                    (review.get("reviewer") or {})
                    .get("profile", {})
                    .get("nickname", "익명")
                )
                body_text = (review.get("reviewer") or {}).get("body_text", "")
                height, weight = _parse_body_text(body_text)

                options = (review.get("product_info") or {}).get("option_detail_list", [])
                size_bought = ", ".join(o["value"] for o in options if o.get("value")) or None

                reviews.append(Review(
                    product_id=product_id,
                    product_name=product_name,
                    image_url=image_url,
                    reviewer=nickname,
                    rating=int(review.get("rating") or 0),
                    body=body,
                    size_bought=size_bought,
                    height=height,
                    weight=weight,
                    created_at="",
                ))

                if len(reviews) >= max_reviews:
                    break

            if not has_next:
                break

            await asyncio.sleep(random.uniform(1.0, 2.0))

    return reviews


_FIT_QUERY = """
query GetReviewSearchList($input: UxReviewSearchListInput!) {
  ux_review_search_list(input: $input) {
    has_next
    end_cursor
    component_list {
      type
      ... on UxReviewListItem {
        review {
          reviewer {
            body_text
          }
          product_info {
            option_detail_list {
              name
              value
            }
          }
          attribute_list {
            question {
              category
            }
            answer {
              value
            }
          }
        }
      }
    }
  }
}
"""


@dataclass
class FitReview:
    height: Optional[int]
    weight: Optional[int]
    size_bought: Optional[str]
    fit_raw_label: Optional[str]  # 예: "FIT", "SMALL", "BIG"


async def _fetch_fit_page(
    client: httpx.AsyncClient,
    product_id: str,
    cursor: Optional[str],
) -> tuple[list[dict], bool, Optional[str]]:
    variables: dict = {
        "input": {
            "product_id": product_id,
            "order": "SCORE_DESC",
            "body_filter": {
                "my_body_filter_checked": False,
                "similar_body_filter_checked": False,
                "option_list": [],
                "has_my_body_reviews": None,
            },
            "option_detail_list": [],
            "topic_list": [],
            "type_list": [],
            "cursor": {"end_cursor": cursor, "limit_count": 20},
        }
    }
    payload = [{"operationName": "GetReviewSearchList", "query": _FIT_QUERY, "variables": variables}]
    try:
        resp = await client.post(_GQL_URL, json=payload, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        data = body[0].get("data", {}).get("ux_review_search_list", {})
        items = data.get("component_list", [])
        has_next = data.get("has_next", False)
        end_cursor = data.get("end_cursor")
        return items, has_next, end_cursor
    except Exception:
        return [], False, None


def _height_weight_from_body_text(body_text: str) -> tuple[Optional[int], Optional[int]]:
    height_str, weight_str = _parse_body_text(body_text)
    height = int(height_str.replace("cm", "")) if height_str else None
    weight = int(weight_str.replace("kg", "")) if weight_str else None
    return height, weight


async def crawl_fit_reviews(
    product_id: str,
    max_reviews: int = 200,
) -> list[FitReview]:
    """체형 유사 추천용 핏 데이터(키/몸무게/구매사이즈/사이즈 만족도)를 수집합니다."""
    fit_reviews: list[FitReview] = []
    cursor: Optional[str] = None

    async with httpx.AsyncClient() as client:
        while len(fit_reviews) < max_reviews:
            items, has_next, cursor = await _fetch_fit_page(client, product_id, cursor)
            if not items:
                break

            for item in items:
                if item.get("type") != "REVIEW_SEARCH_ITEM":
                    continue
                review = item.get("review")
                if not review:
                    continue

                body_text = (review.get("reviewer") or {}).get("body_text", "")
                height, weight = _height_weight_from_body_text(body_text)

                options = (review.get("product_info") or {}).get("option_detail_list", [])
                size_bought = next((o.get("value") for o in options if o.get("name") == "사이즈"), None)

                fit_raw_label = None
                for attr in review.get("attribute_list") or []:
                    if (attr.get("question") or {}).get("category") == "사이즈":
                        fit_raw_label = (attr.get("answer") or {}).get("value")
                        break

                fit_reviews.append(FitReview(
                    height=height,
                    weight=weight,
                    size_bought=size_bought,
                    fit_raw_label=fit_raw_label,
                ))

                if len(fit_reviews) >= max_reviews:
                    break

            if not has_next:
                break

            await asyncio.sleep(random.uniform(1.0, 2.0))

    return fit_reviews


if __name__ == "__main__":
    import json

    async def main():
        results = await crawl_product_reviews("114747784", max_reviews=10)
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))

    asyncio.run(main())
