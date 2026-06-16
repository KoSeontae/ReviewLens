"""
체형 유사 리뷰 추천.

ABSA 13속성 분석과는 완전히 분리된 기능입니다. 쇼핑몰별로 다르게 내려오는
"사이즈가 어땠는지" 신호(에이블리 size_rate, 무신사 설문, 지그재그 attribute_list,
하이버 wearing_sensation)를 small/fit/big 3단계로 정규화한 뒤, 입력한 키/몸무게와
비슷한 리뷰만 모아 구매 사이즈·핏 만족도 비율을 텍스트로 추천합니다.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Literal, Optional

FitVerdict = Literal["small", "fit", "big", "unknown"]

_FIT_LABEL_KR: dict[FitVerdict, str] = {
    "small": "작아요",
    "fit": "잘 맞아요",
    "big": "커요",
}


@dataclass
class FitReview:
    height: Optional[int]
    weight: Optional[int]
    size_bought: Optional[str]
    fit_verdict: FitVerdict


def normalize_fit_label(source: str, raw_label) -> FitVerdict:
    """쇼핑몰별 원본 핏 신호를 small/fit/big/unknown으로 정규화합니다."""
    if raw_label is None:
        return "unknown"

    if source == "ably":
        # size_rate: 0~4 (2가 중심값/정사이즈로 추정)
        try:
            rate = int(raw_label)
        except (TypeError, ValueError):
            return "unknown"
        if rate <= 1:
            return "small"
        if rate == 2:
            return "fit"
        return "big"

    if source == "zigzag":
        mapping: dict[str, FitVerdict] = {"SMALL": "small", "FIT": "fit", "BIG": "big"}
        return mapping.get(str(raw_label).upper(), "unknown")

    # musinsa, hiver: 한글 텍스트 라벨
    text = str(raw_label)
    if "작" in text:
        return "small"
    if "커" in text or "크" in text:
        return "big"
    if "맞" in text or "정사이즈" in text or "적당" in text or "보통" in text:
        return "fit"
    return "unknown"


def build_recommendation(
    fit_reviews: list[FitReview],
    height: int,
    weight: int,
    height_tolerance: int = 3,
    weight_tolerance: int = 4,
) -> dict:
    """입력 체형과 비슷한 리뷰를 골라 사이즈/핏 분포와 추천 텍스트를 만듭니다."""
    similar = [
        r for r in fit_reviews
        if r.height is not None and r.weight is not None
        and abs(r.height - height) <= height_tolerance
        and abs(r.weight - weight) <= weight_tolerance
    ]

    if not similar:
        return {
            "sample_count": 0,
            "size_distribution": [],
            "fit_distribution": [],
            "text": "비슷한 체형(키/몸무게)의 리뷰를 찾지 못했어요. 리뷰가 더 쌓이면 다시 시도해보세요.",
        }

    size_counter = Counter(r.size_bought for r in similar if r.size_bought)
    fit_counter = Counter(r.fit_verdict for r in similar if r.fit_verdict != "unknown")

    total_size = sum(size_counter.values()) or 1
    size_distribution = [
        {"label": label, "count": count, "ratio": round(count / total_size * 100)}
        for label, count in size_counter.most_common()
    ]

    total_fit = sum(fit_counter.values()) or 1
    fit_distribution = [
        {"label": _FIT_LABEL_KR[verdict], "count": count, "ratio": round(count / total_fit * 100)}
        for verdict, count in fit_counter.most_common()
    ]

    parts = [f"나와 비슷한 체형({height}cm·{weight}kg 전후) 구매자 {len(similar)}명을 분석했어요."]
    if size_distribution:
        top_size = size_distribution[0]
        parts.append(f"이 중 {top_size['ratio']}%가 '{top_size['label']}' 사이즈를 구매했고,")
    if fit_distribution:
        top_fit = fit_distribution[0]
        parts.append(f"{top_fit['ratio']}%가 '{top_fit['label']}'라고 답했습니다.")
    if not size_distribution and not fit_distribution:
        parts.append("다만 사이즈·핏 만족도 데이터는 충분하지 않았어요.")

    return {
        "sample_count": len(similar),
        "size_distribution": size_distribution,
        "fit_distribution": fit_distribution,
        "text": " ".join(parts),
    }
