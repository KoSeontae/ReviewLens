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

    def analyze(self, text: str) -> dict[str, float]:
        from analysis.aspects import FASHION_ASPECTS

        sentences = re.split(r"[.!?。\n]+", text)
        scores: dict[str, list[float]] = {}

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 4:
                continue
            score = self._sentence_score(sent)
            for fa in FASHION_ASPECTS:
                if any(kw in sent for kw in fa.keywords):
                    scores.setdefault(fa.key, []).append(score)

        return {k: sum(v) / len(v) for k, v in scores.items()}


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


def analyze_reviews(reviews: list[str]) -> dict[str, float]:
    """
    리뷰 목록을 받아 속성별 평균 감성 점수를 반환합니다.

    Returns:
        {"fit": 0.82, "material": 0.74, ...}  — 해당 속성 언급 없으면 키 없음
    """
    analyzer = get_analyzer()
    aggregated: dict[str, list[float]] = {}

    for review in reviews:
        result = analyzer.analyze(review)
        for key, score in result.items():
            aggregated.setdefault(key, []).append(score)

    return {k: round(sum(v) / len(v), 4) for k, v in aggregated.items()}
