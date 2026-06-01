"""
ABSA(Aspect-Based Sentiment Analysis) 모듈.

전략:
1. PyABSA의 다국어 모델로 속성-감성 쌍 추출 (1차 시도)
2. PyABSA 로드 실패 시, KoELECTRA 기반 감성 분류 + 키워드 매칭으로 폴백

결과 스키마:
  {aspect_key: score}  — score는 0.0~1.0 (1.0 = 매우 긍정)
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 속성별 감성 점수 집계
# ---------------------------------------------------------------------------

def _sentiment_to_score(label: str, confidence: float) -> float:
    """ABSA 레이블을 0~1 점수로 변환."""
    label_lower = label.lower()
    if "pos" in label_lower:
        return 0.5 + confidence * 0.5
    if "neg" in label_lower:
        return 0.5 - confidence * 0.5
    return 0.5  # neutral


# ---------------------------------------------------------------------------
# PyABSA 전략
# ---------------------------------------------------------------------------

class PyABSAAnalyzer:
    def __init__(self):
        from pyabsa import AspectTermExtraction as ATE
        self._extractor = ATE.AspectExtractor("multilingual", auto_device=True)
        logger.info("PyABSA multilingual model loaded.")

    def analyze(self, text: str) -> dict[str, float]:
        """리뷰 한 문장에서 속성-감성 쌍 추출 → aspect_key: score."""
        from analysis.aspects import FASHION_ASPECTS

        try:
            result = self._extractor.predict(text, print_result=False)
        except Exception as e:
            logger.warning("PyABSA prediction failed: %s", e)
            return {}

        # result 구조: {"aspect": [...], "sentiment": [...], "confidence": [...]}
        aspects_found = result.get("aspect", [])
        sentiments = result.get("sentiment", [])
        confidences = result.get("confidence", [])

        scores: dict[str, list[float]] = {}

        for aspect_text, sentiment, conf in zip(aspects_found, sentiments, confidences):
            for fa in FASHION_ASPECTS:
                if any(kw in aspect_text for kw in fa.keywords):
                    scores.setdefault(fa.key, []).append(
                        _sentiment_to_score(sentiment, float(conf))
                    )

        return {k: sum(v) / len(v) for k, v in scores.items()}


# ---------------------------------------------------------------------------
# KoELECTRA 폴백 전략
# ---------------------------------------------------------------------------

class KoELECTRAAnalyzer:
    """
    monologg/koelectra-base-finetuned-sentiment 모델을 이용한
    문장 단위 감성 분류 + 키워드 기반 속성 매핑.
    """

    MODEL_NAME = "monologg/koelectra-base-finetuned-sentiment"

    def __init__(self):
        from transformers import pipeline
        self._pipe = pipeline(
            "text-classification",
            model=self.MODEL_NAME,
            tokenizer=self.MODEL_NAME,
            top_k=None,
        )
        logger.info("KoELECTRA sentiment model loaded.")

    def _sentence_score(self, text: str) -> float:
        """문장 전체 감성 점수 (0~1)."""
        try:
            outputs = self._pipe(text[:512])[0]
            label_score = {o["label"]: o["score"] for o in outputs}
            pos = label_score.get("positive", label_score.get("POSITIVE", 0.5))
            return float(pos)
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

_analyzer: Optional[PyABSAAnalyzer | KoELECTRAAnalyzer] = None


def get_analyzer() -> PyABSAAnalyzer | KoELECTRAAnalyzer:
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = PyABSAAnalyzer()
        except Exception as e:
            logger.warning("PyABSA unavailable (%s), falling back to KoELECTRA.", e)
            _analyzer = KoELECTRAAnalyzer()
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
