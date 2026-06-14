"""
ABSA(Aspect-Based Sentiment Analysis) 모듈.

전략:
1. PyABSA의 다국어 모델로 속성-감성 쌍 추출 (1차 시도)
2. PyABSA 로드 실패 시, hun3359/klue-bert-base-sentiment 모델로 폴백
   - 한국어 감정 분류 모델 (60개 감정 레이블)
   - 긍정/부정 감정 그룹으로 매핑 후 속성별 점수 산출

결과 스키마:
  {aspect_key: score}  — score는 0.0~1.0 (1.0 = 매우 긍정)
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

# 긍정 감정 레이블
_POSITIVE_LABELS = {
    "만족스러운", "기쁨", "신뢰하는", "편안한", "느긋", "신이 난",
    "감사하는", "자신하는", "안도", "흥분",
}

# 부정 감정 레이블
_NEGATIVE_LABELS = {
    "실망한", "낙담한", "툴툴대는", "좌절한", "슬픔", "분노",
    "짜증내는", "환멸을 느끼는", "우울한", "후회되는", "배신당한",
    "한심한", "혐오스러운", "구역질 나는", "스트레스 받는", "당황",
    "당혹스러운", "충격 받은", "비통한", "억울한", "눈물이 나는",
}


def _extract_relevant_clause(sentence: str, keywords: list[str]) -> str:
    """문장을 절 단위로 분리해 해당 속성 키워드가 포함된 절만 반환."""
    # 쉼표 또는 접속 어미(고/며/지만/는데/어서/아서) 뒤에서 분리
    parts = re.split(r"[,，]\s*|(?<=[고며])\s+|(?<=지만)\s+|(?<=는데)\s+|(?<=어서)\s+|(?<=아서)\s+", sentence)

    relevant = [p.strip() for p in parts if len(p.strip()) >= 5 and any(kw in p for kw in keywords)]
    return " / ".join(relevant) if relevant else sentence.strip()


def _labels_to_score(outputs: list[dict]) -> float:
    """감정 레이블 목록을 0~1 점수로 변환."""
    pos_score = sum(o["score"] for o in outputs if o["label"] in _POSITIVE_LABELS)
    neg_score = sum(o["score"] for o in outputs if o["label"] in _NEGATIVE_LABELS)
    total = pos_score + neg_score
    if total < 0.05:
        return 0.5  # 긍/부정 신호 모두 약하면 중립
    return pos_score / total


# ---------------------------------------------------------------------------
# PyABSA 전략
# ---------------------------------------------------------------------------

class PyABSAAnalyzer:
    def __init__(self):
        from pyabsa import AspectTermExtraction as ATE
        self._extractor = ATE.AspectExtractor("multilingual", auto_device=True)
        logger.info("PyABSA multilingual model loaded.")

    def analyze(self, text: str) -> dict[str, float]:
        from analysis.aspects import FASHION_ASPECTS
        try:
            result = self._extractor.predict(text, print_result=False)
        except Exception as e:
            logger.warning("PyABSA prediction failed: %s", e)
            return {}

        aspects_found = result.get("aspect", [])
        sentiments = result.get("sentiment", [])
        confidences = result.get("confidence", [])
        scores: dict[str, list[float]] = {}

        for aspect_text, sentiment, conf in zip(aspects_found, sentiments, confidences):
            label_lower = sentiment.lower()
            if "pos" in label_lower:
                score = 0.5 + float(conf) * 0.5
            elif "neg" in label_lower:
                score = 0.5 - float(conf) * 0.5
            else:
                score = 0.5
            for fa in FASHION_ASPECTS:
                if any(kw in aspect_text for kw in fa.keywords):
                    scores.setdefault(fa.key, []).append(score)

        return {k: sum(v) / len(v) for k, v in scores.items()}


# ---------------------------------------------------------------------------
# KLUE-BERT 감정 분류 폴백 전략
# ---------------------------------------------------------------------------

class KlueBertAnalyzer:
    """
    hun3359/klue-bert-base-sentiment 모델을 이용한
    한국어 감정 분류 + 키워드 기반 속성 매핑.
    60개 감정 레이블을 긍정/부정 그룹으로 매핑해 속성별 점수를 산출합니다.
    """

    MODEL_NAME = "hun3359/klue-bert-base-sentiment"

    def __init__(self):
        from transformers import pipeline
        self._pipe = pipeline(
            "text-classification",
            model=self.MODEL_NAME,
            tokenizer=self.MODEL_NAME,
            top_k=None,
        )
        logger.info("KLUE-BERT sentiment model loaded.")

    def _sentence_score(self, text: str) -> float:
        try:
            outputs = self._pipe(text[:512])[0]
            return _labels_to_score(outputs)
        except Exception:
            return 0.5

    def analyze(self, text: str) -> tuple[dict[str, float], dict[str, list[str]]]:
        from analysis.aspects import FASHION_ASPECTS

        sentences = re.split(r"[.!?。\n]+", text)
        scores: dict[str, list[float]] = {}
        snippets: dict[str, list[str]] = {}

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 4:
                continue
            score = self._sentence_score(sent)
            for fa in FASHION_ASPECTS:
                if any(kw in sent for kw in fa.keywords):
                    scores.setdefault(fa.key, []).append(score)
                    clause = _extract_relevant_clause(sent, fa.keywords)
                    snippets.setdefault(fa.key, []).append(clause)

        return {k: sum(v) / len(v) for k, v in scores.items()}, snippets


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

_analyzer: Optional[PyABSAAnalyzer | KlueBertAnalyzer] = None


def get_analyzer() -> PyABSAAnalyzer | KlueBertAnalyzer:
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = PyABSAAnalyzer()
        except Exception as e:
            logger.warning("PyABSA unavailable (%s), falling back to KLUE-BERT.", e)
            _analyzer = KlueBertAnalyzer()
    return _analyzer


_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "fit": {
        "high": ["핏감이 좋다는 평이 많습니다", "실루엣이 예쁘다는 반응이 많습니다", "핏이 마음에 든다는 의견이 많습니다"],
        "mid":  ["핏이 무난하다는 반응입니다", "핏에 대해 보통이라는 의견이 많습니다"],
        "low":  ["핏이 기대와 다르다는 의견이 있습니다", "핏에 아쉬움을 표한 리뷰가 많습니다"],
    },
    "material": {
        "high": ["소재 만족도가 높습니다", "원단이 좋다는 평이 많습니다", "소재가 부드럽다는 반응이 많습니다"],
        "mid":  ["소재가 무난하다는 의견입니다", "소재가 평범하다는 반응입니다"],
        "low":  ["소재에 대한 아쉬움이 언급됩니다", "원단 품질에 불만족한 리뷰가 있습니다"],
    },
    "finish": {
        "high": ["마감 품질이 좋다는 평이 많습니다", "봉제와 마감이 탄탄하다는 반응입니다", "완성도가 높다는 의견이 많습니다"],
        "mid":  ["마감이 보통 수준이라는 의견입니다", "마감에 대해 무난하다는 반응입니다"],
        "low":  ["마감 품질에 아쉬움을 표한 리뷰가 있습니다", "봉제 불량을 언급한 리뷰가 있습니다"],
    },
    "size": {
        "high": ["사이즈가 잘 맞는다는 반응이 많습니다", "사이즈 표기가 정확하다는 의견입니다"],
        "mid":  ["사이즈가 약간 크거나 작다는 의견이 있습니다", "사이즈 편차가 있다는 반응입니다"],
        "low":  ["사이즈가 맞지 않는다는 의견이 많습니다", "사이즈 불만족 리뷰가 다수입니다"],
    },
    "price": {
        "high": ["가성비가 좋다는 반응이 많습니다", "가격 대비 만족도가 높습니다"],
        "mid":  ["가격이 적당하다는 의견입니다", "가성비가 무난하다는 반응입니다"],
        "low":  ["가격 대비 아쉽다는 의견이 있습니다", "가성비에 불만족한 리뷰가 있습니다"],
    },
    "color": {
        "high": ["실물 색상이 사진과 비슷하다는 반응이 많습니다", "색감 만족도가 높습니다"],
        "mid":  ["색상이 사진과 약간 다르다는 의견이 있습니다"],
        "low":  ["실물 색상이 사진과 다르다는 의견이 많습니다", "색감 차이를 언급한 리뷰가 많습니다"],
    },
    "design": {
        "high": ["디자인이 예쁘다는 반응이 많습니다", "스타일이 세련됐다는 평이 많습니다"],
        "mid":  ["디자인이 무난하다는 의견입니다", "평범한 디자인이라는 반응입니다"],
        "low":  ["디자인에 아쉬움을 표한 리뷰가 있습니다"],
    },
    "comfort": {
        "high": ["착용감이 편안하다는 반응이 많습니다", "입었을 때 편하다는 평이 많습니다"],
        "mid":  ["착용감이 무난하다는 의견입니다"],
        "low":  ["착용감이 불편하다는 의견이 있습니다", "불편함을 언급한 리뷰가 있습니다"],
    },
    "delivery": {
        "high": ["배송이 빠르다는 반응이 많습니다", "배송 및 포장 만족도가 높습니다"],
        "mid":  ["배송이 보통 수준이라는 의견입니다"],
        "low":  ["배송이 느리다는 의견이 있습니다", "배송 관련 불만이 언급됩니다"],
    },
    "care": {
        "high": ["세탁 후 변형이 없다는 반응이 많습니다", "관리가 편하다는 의견입니다"],
        "mid":  ["세탁 관리가 무난하다는 의견입니다"],
        "low":  ["세탁 후 변형을 언급한 리뷰가 있습니다", "보풀이나 탈색을 언급한 리뷰가 있습니다"],
    },
    "sheerness": {
        "high": ["비침이 없다는 반응이 많습니다", "속이 비치지 않는다는 평이 많습니다"],
        "mid":  ["비침이 약간 있다는 의견이 있습니다"],
        "low":  ["비침이 있다는 의견이 많습니다", "속이 비친다는 언급이 많습니다"],
    },
    "stretch": {
        "high": ["신축성이 좋다는 반응이 많습니다", "스판감이 있어 편하다는 평입니다"],
        "mid":  ["신축성이 보통 수준이라는 의견입니다"],
        "low":  ["신축성이 부족하다는 의견이 있습니다", "잘 늘어나지 않는다는 반응입니다"],
    },
    "season": {
        "high": ["계절감이 잘 맞는다는 반응이 많습니다", "해당 계절에 입기 좋다는 평이 많습니다"],
        "mid":  ["사계절 활용 가능하다는 반응입니다", "계절을 타지 않는다는 의견입니다"],
        "low":  ["계절감이 맞지 않는다는 의견이 있습니다"],
    },
}


def _build_summary(key: str, score: float, clauses: list[str], aspect_keywords: list[str]) -> str:
    """점수와 가장 많이 언급된 키워드를 바탕으로 템플릿 문장을 선택합니다."""
    templates = _TEMPLATES.get(key, {})
    if score >= 0.72:
        options = templates.get("high", [])
    elif score >= 0.48:
        options = templates.get("mid", [])
    else:
        options = templates.get("low", [])

    if not options:
        return ""

    # 가장 자주 언급된 키워드로 템플릿 인덱스 결정
    kw_counter: Counter[str] = Counter()
    for clause in clauses:
        for kw in aspect_keywords:
            if kw in clause:
                kw_counter[kw] += 1

    # 키워드 빈도에 따라 여러 템플릿 중 선택 (다양성 확보)
    idx = min(len(kw_counter) % len(options), len(options) - 1) if kw_counter else 0
    return options[idx]


def analyze_reviews(reviews: list[str]) -> tuple[dict[str, float], dict[str, str]]:
    """
    리뷰 목록을 받아 속성별 평균 감성 점수와 대표 문장 요약을 반환합니다.

    Returns:
        scores: {"fit": 0.82, "material": 0.74, ...}
        summaries: {"fit": "핏이 예뻐요 / 오버핏이라 좋아요", ...}
    """
    analyzer = get_analyzer()
    aggregated: dict[str, list[float]] = {}
    all_snippets: dict[str, list[str]] = {}

    for review in reviews:
        scores, snippets = analyzer.analyze(review)
        for key, score in scores.items():
            aggregated.setdefault(key, []).append(score)
        for key, sents in snippets.items():
            all_snippets.setdefault(key, []).extend(sents)

    scores_out = {k: round(sum(v) / len(v), 4) for k, v in aggregated.items()}

    from analysis.aspects import FASHION_ASPECTS
    aspect_kw_map = {a.key: a.keywords for a in FASHION_ASPECTS}

    summaries: dict[str, str] = {
        key: _build_summary(key, score, all_snippets.get(key, []), aspect_kw_map.get(key, []))
        for key, score in scores_out.items()
    }

    return scores_out, summaries
