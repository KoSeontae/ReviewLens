"""
ABSA(Aspect-Based Sentiment Analysis) 모듈.

전략:
1. PyABSA의 다국어 모델로 속성-감성 쌍 추출 (1차 시도)
2. PyABSA 로드 실패 시, HuggingFace Inference API로 폴백
   - hun3359/klue-bert-base-sentiment 모델 (HF 서버 GPU에서 실행)
   - 60개 감정 레이블을 긍정/부정 그룹으로 매핑 후 속성별 점수 산출

결과 스키마:
  {aspect_key: score}  — score는 0.0~1.0 (1.0 = 매우 긍정)
"""

from __future__ import annotations

import logging
import os
import re
import time
from collections import Counter
from typing import Callable, Optional

import httpx

logger = logging.getLogger(__name__)

HF_API_URL = "https://router.huggingface.co/hf-inference/models/hun3359/klue-bert-base-sentiment"
HF_TOKEN = os.getenv("HF_TOKEN", "")

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
    HuggingFace Inference API를 통해 hun3359/klue-bert-base-sentiment 모델 호출.
    문장 배치를 한 번에 전송해 네트워크 왕복을 최소화합니다.
    """

    def __init__(self):
        if not HF_TOKEN:
            raise ValueError("HF_TOKEN 환경변수가 설정되지 않았습니다.")
        logger.info("KlueBertAnalyzer initialized (HF Inference API).")

    def _call_api(self, sentences: list[str]) -> list[list[dict]]:
        """배치 문장을 HF Inference API에 전송하고 결과를 반환합니다. 콜드 스타트 시 재시도."""
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": sentences, "parameters": {"top_k": None}}

        for attempt in range(3):
            response = httpx.post(HF_API_URL, headers=headers, json=payload, timeout=60.0)
            if response.status_code == 200:
                result = response.json()
                # 단일 문자열 입력 시 list[dict]로 반환되므로 통일
                if result and isinstance(result[0], dict):
                    return [result]
                return result
            if response.status_code == 503:
                # 모델 로딩 중 (콜드 스타트) — 최대 20초 대기 후 재시도
                wait = response.json().get("estimated_time", 20)
                logger.info("HF 모델 로딩 중, %.0f초 대기 (시도 %d/3)", wait, attempt + 1)
                time.sleep(min(wait, 20))
            else:
                logger.error("HF API 오류 %d: %s", response.status_code, response.text)
                break

        return [[] for _ in sentences]

    def score_sentences(
        self,
        sentences: list[str],
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> list[float]:
        """문장 리스트를 32개씩 배치로 나눠 API에 전송하고 점수 리스트를 반환합니다."""
        BATCH_SIZE = 32
        total = len(sentences)
        scores: list[float] = []
        for i in range(0, total, BATCH_SIZE):
            batch = [s[:256] for s in sentences[i : i + BATCH_SIZE]]
            results = self._call_api(batch)
            scores.extend(_labels_to_score(outputs) if outputs else 0.5 for outputs in results)
            if on_progress:
                on_progress(min(i + BATCH_SIZE, total), total)
        return scores

    def analyze(self, text: str) -> tuple[dict[str, float], dict[str, list[str]]]:
        from analysis.aspects import FASHION_ASPECTS

        sentences = [s.strip() for s in re.split(r"[.!?。\n]+", text) if len(s.strip()) >= 4]
        if not sentences:
            return {}, {}

        sentence_scores = self.score_sentences(sentences)
        aspect_scores: dict[str, list[float]] = {}
        snippets: dict[str, list[str]] = {}

        for sent, score in zip(sentences, sentence_scores):
            for fa in FASHION_ASPECTS:
                if any(kw in sent for kw in fa.keywords):
                    aspect_scores.setdefault(fa.key, []).append(score)
                    snippets.setdefault(fa.key, []).append(_extract_relevant_clause(sent, fa.keywords))

        return {k: sum(v) / len(v) for k, v in aspect_scores.items()}, snippets


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
            logger.warning("PyABSA unavailable (%s), falling back to HF Inference API.", e)
            _analyzer = KlueBertAnalyzer()
    return _analyzer


# 키워드별 세부 템플릿 (top 키워드가 있을 때 우선 사용)
_KEYWORD_TEMPLATES: dict[str, dict[str, str]] = {
    # 핏
    "오버핏":   {"high": "오버핏이 잘 살아있어 여유롭게 입기 좋다는 반응이 많습니다",     "mid": "오버핏이지만 체형에 따라 느낌이 다를 수 있습니다",              "low": "오버핏 정도가 사진과 달라 주의가 필요하다는 의견이 있습니다"},
    "슬림핏":   {"high": "슬림핏으로 라인이 예쁘게 살아난다는 반응이 많습니다",           "mid": "슬림핏이라 체형에 따라 한 사이즈 업을 권장하는 의견이 있습니다", "low": "슬림핏이 너무 타이트하다는 의견이 있어 사이즈 선택에 주의하세요"},
    "정핏":     {"high": "정핏으로 체형에 잘 맞는다는 반응이 많습니다",                   "mid": "정핏이지만 체형에 따라 조금씩 다르게 느껴질 수 있습니다",        "low": "정핏이지만 실제로는 사이즈 차이가 있다는 의견이 있습니다"},
    "루즈핏":   {"high": "루즈핏으로 편안하게 입을 수 있다는 반응이 많습니다",             "mid": "루즈핏으로 약간 크게 느껴질 수 있다는 의견이 있습니다",          "low": "루즈핏이 과도하게 커서 불편하다는 의견이 있습니다"},
    "타이트핏": {"high": "타이트핏으로 몸에 잘 맞는다는 반응이 많습니다",                 "mid": "타이트핏이라 체형에 따라 불편할 수 있다는 의견이 있습니다",       "low": "타이트핏이 너무 조인다는 의견이 있어 한 사이즈 업을 권장합니다"},
    "실루엣":   {"high": "실루엣이 예쁘게 잡힌다는 반응이 많습니다",                      "mid": "실루엣이 무난하다는 의견이 많습니다",                            "low": "실루엣이 기대와 다르다는 의견이 있습니다"},
    # 소재
    "순면":     {"high": "순면 소재라 피부에 부드럽고 착용감이 좋다는 반응이 많습니다",    "mid": "순면 소재이지만 주름이 잘 생길 수 있다는 의견이 있습니다",        "low": "순면 소재인데도 촉감이 아쉽다는 의견이 있습니다"},
    "코튼":     {"high": "코튼 소재라 가볍고 편하다는 반응이 많습니다",                    "mid": "코튼 소재로 무난하다는 의견이 많습니다",                          "low": "코튼 소재이지만 품질이 기대에 못 미친다는 의견이 있습니다"},
    "울소재":   {"high": "울 소재로 보온성이 뛰어나다는 반응이 많습니다",                  "mid": "울 소재이지만 따뜻함이 기대만큼은 아니라는 의견이 있습니다",       "low": "울 소재인데도 품질이 아쉽다는 의견이 있습니다"},
    "폴리":     {"high": "폴리 소재라 구김이 적고 관리가 쉽다는 반응이 많습니다",          "mid": "폴리 소재로 가격 대비 무난하다는 의견이 많습니다",               "low": "폴리 소재 특유의 질감이 아쉽다는 의견이 있습니다"},
    "촉감":     {"high": "촉감이 부드러워 만족스럽다는 반응이 많습니다",                   "mid": "촉감이 무난한 편이라는 의견이 많습니다",                          "low": "촉감이 거칠거나 불편하다는 의견이 있습니다"},
    "두께감":   {"high": "두께감이 적절해 계절감이 잘 맞는다는 반응이 많습니다",           "mid": "두께감이 기대와 약간 다를 수 있다는 의견이 있습니다",             "low": "두께감이 너무 얇거나 두껍다는 의견이 있어 참고하세요"},
    # 마감
    "박음질":   {"high": "박음질이 꼼꼼하고 튼튼하다는 반응이 많습니다",                   "mid": "박음질이 무난한 수준이라는 의견입니다",                           "low": "박음질이 고르지 않다는 의견이 있으니 확인이 필요합니다"},
    "봉제":     {"high": "봉제 상태가 깔끔하다는 반응이 많습니다",                         "mid": "봉제가 평균적인 수준이라는 의견입니다",                           "low": "봉제 불량이 있다는 의견이 있어 수령 후 확인을 권장합니다"},
    "실밥":     {"high": "실밥 처리가 깔끔하다는 반응이 많습니다",                         "mid": "실밥 처리가 무난한 수준이라는 의견입니다",                        "low": "실밥이 지저분하다는 의견이 있으니 수령 후 확인하세요"},
    "올풀림":   {"high": "올풀림 없이 마감이 깔끔하다는 반응이 많습니다",                   "mid": "올풀림이 약간 있을 수 있다는 의견이 있습니다",                    "low": "올풀림이 생겼다는 의견이 있어 주의가 필요합니다"},
    "내구성":   {"high": "내구성이 좋아 오래 입을 수 있다는 반응이 많습니다",               "mid": "내구성이 무난한 편이라는 의견입니다",                             "low": "내구성이 기대에 못 미친다는 의견이 있습니다"},
    "퀄리티":   {"high": "전반적인 퀄리티가 가격 대비 높다는 반응이 많습니다",              "mid": "퀄리티가 가격 대비 무난하다는 의견입니다",                        "low": "퀄리티가 가격 대비 아쉽다는 의견이 있습니다"},
    "완성도":   {"high": "전체적인 완성도가 높다는 반응이 많습니다",                        "mid": "완성도가 무난한 수준이라는 의견입니다",                           "low": "완성도가 기대보다 낮다는 의견이 있습니다"},
    # 사이즈
    "사이즈표": {"high": "사이즈표와 실제 치수가 잘 맞는다는 반응이 많습니다",              "mid": "사이즈표와 약간 차이가 있을 수 있다는 의견이 있습니다",           "low": "사이즈표와 실제 치수 차이가 있다는 의견이 많아 주의가 필요합니다"},
    "실측":     {"high": "실측이 정확하다는 반응이 많습니다",                               "mid": "실측이 약간 차이가 날 수 있다는 의견이 있습니다",                "low": "실측이 표기와 다르다는 의견이 있어 구매 전 확인을 권장합니다"},
    "기장":     {"high": "기장이 적절하다는 반응이 많습니다",                               "mid": "기장이 체형에 따라 길거나 짧을 수 있다는 의견이 있습니다",        "low": "기장이 기대와 다르다는 의견이 있어 참고하세요"},
    "어깨너비": {"high": "어깨너비가 잘 맞는다는 반응이 많습니다",                          "mid": "어깨너비가 체형에 따라 다르게 느껴질 수 있다는 의견이 있습니다",  "low": "어깨너비가 맞지 않는다는 의견이 있어 치수를 꼭 확인하세요"},
    # 가격
    "가성비":   {"high": "가성비가 뛰어나다는 반응이 많습니다",                             "mid": "가성비가 무난하다는 의견이 많습니다",                             "low": "가성비가 아쉽다는 의견이 있습니다"},
    "합리적":   {"high": "가격이 합리적이라는 반응이 많습니다",                             "mid": "가격이 평범하다는 의견이 많습니다",                               "low": "가격 대비 만족도가 낮다는 의견이 있습니다"},
    "값어치":   {"high": "값어치를 충분히 한다는 반응이 많습니다",                          "mid": "값어치가 무난하다는 의견이 많습니다",                             "low": "값어치가 아쉽다는 의견이 있습니다"},
    "돈값":     {"high": "돈값을 충분히 한다는 반응이 많습니다",                            "mid": "돈값이 애매하다는 의견도 있습니다",                               "low": "돈값을 못한다는 의견이 있습니다"},
    # 색상
    "색감":     {"high": "색감이 사진과 비슷하고 실물도 예쁘다는 반응이 많습니다",          "mid": "색감이 사진과 약간 다를 수 있다는 의견이 있습니다",               "low": "색감이 사진과 많이 다르다는 의견이 있어 참고하세요"},
    "색톤":     {"high": "색톤이 사진과 일치한다는 반응이 많습니다",                        "mid": "색톤이 모니터에 따라 다르게 보일 수 있다는 의견이 있습니다",      "low": "색톤이 사진과 많이 다르다는 의견이 있습니다"},
    "보정":     {"high": "보정 없이도 실물 색상이 예쁘다는 반응이 많습니다",                "mid": "사진 보정으로 실물과 약간 다를 수 있다는 의견이 있습니다",         "low": "사진 보정이 심해 실물과 많이 다르다는 의견이 많습니다"},
    "실제색":   {"high": "실제 색상이 사진과 거의 같다는 반응이 많습니다",                  "mid": "실제 색상이 사진과 약간 차이가 있다는 의견이 있습니다",           "low": "실제 색상이 사진과 많이 다르다는 의견이 많아 주의가 필요합니다"},
    # 디자인
    "스타일":   {"high": "스타일이 트렌디하고 예쁘다는 반응이 많습니다",                    "mid": "스타일이 무난하고 활용도가 높다는 의견입니다",                    "low": "스타일이 기대와 다르다는 의견이 있습니다"},
    "패턴":     {"high": "패턴이 예쁘고 세련됐다는 반응이 많습니다",                        "mid": "패턴이 무난하다는 의견이 많습니다",                               "low": "패턴이 사진과 다르다는 의견이 있습니다"},
    "프린트":   {"high": "프린트가 선명하고 예쁘다는 반응이 많습니다",                      "mid": "프린트가 무난하다는 의견이 많습니다",                             "low": "프린트 품질이 아쉽다는 의견이 있습니다"},
    "유니크":   {"high": "유니크한 디자인이 특별함을 더한다는 반응이 많습니다",              "mid": "유니크하지만 호불호가 있을 수 있다는 의견이 있습니다",            "low": "유니크한 디자인이 취향을 타서 기대와 다르다는 의견이 있습니다"},
    "무늬":     {"high": "무늬가 사진과 동일하고 예쁘다는 반응이 많습니다",                 "mid": "무늬가 실물에서 약간 다르게 느껴질 수 있다는 의견이 있습니다",    "low": "무늬가 사진과 다르다는 의견이 있어 참고하세요"},
    # 착용감
    "통기성":   {"high": "통기성이 좋아 더운 날에도 쾌적하다는 반응이 많습니다",            "mid": "통기성이 무난한 편이라는 의견입니다",                             "low": "통기성이 부족해 더울 수 있다는 의견이 있습니다"},
    "보온성":   {"high": "보온성이 뛰어나 추운 날에도 따뜻하다는 반응이 많습니다",          "mid": "보온성이 무난한 편이라는 의견입니다",                             "low": "보온성이 기대에 못 미친다는 의견이 있습니다"},
    "착용감":   {"high": "착용감이 매우 편안하다는 반응이 많습니다",                        "mid": "착용감이 무난하다는 의견입니다",                                  "low": "착용감이 불편하다는 의견이 있어 주의가 필요합니다"},
    "무게감":   {"high": "무게감이 가벼워 편하게 입을 수 있다는 반응이 많습니다",           "mid": "무게감이 적당하다는 의견이 많습니다",                             "low": "무게감이 예상보다 무겁다는 의견이 있습니다"},
    # 배송
    "포장":       {"high": "포장이 꼼꼼하고 상태가 좋다는 반응이 많습니다",                 "mid": "포장이 무난하다는 의견입니다",                                    "low": "포장 상태가 불량하다는 의견이 있습니다"},
    "빠른배송":   {"high": "배송이 매우 빠르다는 반응이 많습니다",                          "mid": "배송 속도가 보통 수준이라는 의견입니다",                          "low": "배송이 예상보다 오래 걸린다는 의견이 있습니다"},
    "배송기간":   {"high": "배송기간이 짧고 빠르다는 반응이 많습니다",                      "mid": "배송기간이 평균적이라는 의견입니다",                              "low": "배송기간이 길다는 의견이 있어 여유롭게 주문하세요"},
    "박스":       {"high": "박스 포장이 튼튼하고 안전하다는 반응이 많습니다",               "mid": "박스 상태가 무난하다는 의견입니다",                               "low": "박스가 찌그러지거나 파손됐다는 의견이 있습니다"},
    # 관리
    "보풀":     {"high": "보풀이 잘 생기지 않는다는 반응이 많습니다",                       "mid": "보풀이 약간 생길 수 있다는 의견이 있습니다",                      "low": "보풀이 생겼다는 의견이 많아 관리에 주의가 필요합니다"},
    "탈색":     {"high": "탈색 없이 색상이 잘 유지된다는 반응이 많습니다",                  "mid": "탈색이 약간 있을 수 있다는 의견이 있습니다",                      "low": "탈색이 생겼다는 의견이 있어 세탁 시 주의가 필요합니다"},
    "필링":     {"high": "필링 없이 깔끔하게 유지된다는 반응이 많습니다",                   "mid": "필링이 약간 생길 수 있다는 의견이 있습니다",                      "low": "필링이 심하다는 의견이 있어 주의가 필요합니다"},
    "변형":     {"high": "세탁 후에도 변형 없이 형태가 유지된다는 반응이 많습니다",         "mid": "세탁 시 약간의 변형이 생길 수 있다는 의견이 있습니다",            "low": "세탁 후 변형이 생겼다는 의견이 있어 주의하세요"},
    "다림질":   {"high": "다림질 없이도 깔끔하게 입을 수 있다는 반응이 많습니다",           "mid": "다림질이 필요할 수 있다는 의견이 있습니다",                       "low": "다림질을 해도 주름이 잘 펴지지 않는다는 의견이 있습니다"},
    # 비침
    "비침":     {"high": "비침이 없어 편하게 입을 수 있다는 반응이 많습니다",               "mid": "비침이 약간 있을 수 있다는 의견이 있습니다",                      "low": "비침이 있어 안에 받쳐 입어야 한다는 의견이 많습니다"},
    "속보임":   {"high": "속이 비치지 않아 단독 착용이 가능하다는 반응이 많습니다",         "mid": "밝은 색상의 경우 약간 속이 보일 수 있다는 의견이 있습니다",       "low": "속이 보여 안에 받쳐 입어야 한다는 의견이 많습니다"},
    "안비침":   {"high": "안비침이 확실해 단독 착용이 가능하다는 반응이 많습니다",          "mid": "빛에 따라 약간 비칠 수 있다는 의견이 있습니다",                   "low": "생각보다 비침이 있다는 의견이 있어 주의가 필요합니다"},
    # 신축성
    "스판":     {"high": "스판감이 좋아 활동하기 편하다는 반응이 많습니다",                 "mid": "스판이 약간 있어 무난하게 입을 수 있다는 의견입니다",             "low": "스판이 부족해 활동이 불편하다는 의견이 있습니다"},
    "탄성":     {"high": "탄성이 좋아 원래 형태로 잘 돌아온다는 반응이 많습니다",           "mid": "탄성이 무난한 수준이라는 의견입니다",                             "low": "탄성이 부족해 금방 늘어진다는 의견이 있습니다"},
    "탄력":     {"high": "탄력이 좋아 오래 입어도 처지지 않는다는 반응이 많습니다",         "mid": "탄력이 무난한 편이라는 의견입니다",                               "low": "탄력이 부족하다는 의견이 있어 참고하세요"},
    # 계절감
    "여름":     {"high": "여름에 입기 딱 좋다는 반응이 많습니다",                           "mid": "여름에 무난하게 입을 수 있다는 의견입니다",                       "low": "여름에 입기에는 너무 두껍다는 의견이 있습니다"},
    "겨울":     {"high": "겨울에 따뜻하게 입기 좋다는 반응이 많습니다",                     "mid": "겨울에 무난하게 입을 수 있다는 의견입니다",                       "low": "겨울에 입기에는 얇다는 의견이 있습니다"},
    "간절기":   {"high": "간절기에 입기 딱 좋다는 반응이 많습니다",                         "mid": "간절기에 무난하게 활용 가능하다는 의견입니다",                    "low": "간절기보다 다른 계절에 더 어울린다는 의견이 있습니다"},
    "사계절":   {"high": "사계절 내내 활용할 수 있다는 반응이 많습니다",                    "mid": "사계절 착용 가능하지만 계절감이 애매하다는 의견도 있습니다",       "low": "사계절 착용이 어렵다는 의견이 있습니다"},
    "봄가을":   {"high": "봄가을에 입기 딱 좋다는 반응이 많습니다",                         "mid": "봄가을에 무난하게 입을 수 있다는 의견입니다",                     "low": "봄가을에 입기에 계절감이 맞지 않는다는 의견이 있습니다"},
}

# 양방향 키워드: 클로즈에서 어느 방향이 더 많이 언급됐는지 감지해 mid/low 템플릿을 교체
_DIRECTION_HINTS: dict[str, dict[str, dict[str, str]]] = {
    "기장": {
        "길": {
            "mid": "기장이 다소 긴 편이라는 의견이 있어 참고하세요",
            "low": "기장이 길다는 의견이 많아 사이즈 선택에 주의하세요",
        },
        "짧": {
            "mid": "기장이 다소 짧은 편이라는 의견이 있어 참고하세요",
            "low": "기장이 짧다는 의견이 많아 참고하세요",
        },
    },
    "어깨너비": {
        "넓": {
            "mid": "어깨너비가 다소 넓은 편이라는 의견이 있습니다",
            "low": "어깨너비가 넓어 맞지 않는다는 의견이 있어 치수를 꼭 확인하세요",
        },
        "좁": {
            "mid": "어깨너비가 다소 좁은 편이라는 의견이 있습니다",
            "low": "어깨너비가 좁다는 의견이 있어 치수를 꼭 확인하세요",
        },
    },
    "두께감": {
        "두껍": {
            "mid": "두께감이 다소 두꺼운 편이라는 의견이 있습니다",
            "low": "두께감이 너무 두껍다는 의견이 있어 참고하세요",
        },
        "얇": {
            "mid": "두께감이 다소 얇은 편이라는 의견이 있습니다",
            "low": "두께감이 너무 얇다는 의견이 있어 참고하세요",
        },
    },
    "실측": {
        "크": {
            "mid": "실측이 표기보다 약간 크게 나온다는 의견이 있어 참고하세요",
            "low": "실측이 표기보다 크게 나온다는 의견이 많아 한 사이즈 다운을 고려하세요",
        },
        "작": {
            "mid": "실측이 표기보다 약간 작게 나온다는 의견이 있어 참고하세요",
            "low": "실측이 표기보다 작게 나온다는 의견이 많아 한 사이즈 업을 고려하세요",
        },
    },
    "사이즈표": {
        "크": {
            "mid": "사이즈표보다 실제로 약간 크게 나온다는 의견이 있습니다",
            "low": "사이즈표보다 실제로 크게 나온다는 의견이 많아 한 사이즈 다운을 고려하세요",
        },
        "작": {
            "mid": "사이즈표보다 실제로 약간 작게 나온다는 의견이 있습니다",
            "low": "사이즈표보다 실제로 작게 나온다는 의견이 많아 한 사이즈 업을 고려하세요",
        },
    },
}

# 키워드가 없을 때 속성별 폴백 템플릿
_ASPECT_TEMPLATES: dict[str, dict[str, str]] = {
    "fit":       {"high": "전반적으로 핏이 예쁘게 떨어진다는 반응이 많습니다",           "mid": "핏은 무난한 편으로, 체형에 따라 호불호가 있을 수 있습니다",        "low": "핏이 기대와 다르다는 의견이 있어 사이즈 선택에 주의하세요"},
    "material":  {"high": "소재가 부드럽고 품질이 좋다는 반응이 많습니다",               "mid": "소재가 가격 대비 무난하다는 의견이 많습니다",                       "low": "소재 품질이 기대에 미치지 못한다는 의견이 있습니다"},
    "finish":    {"high": "박음질과 마감이 꼼꼼하다는 평이 많습니다",                    "mid": "마감 처리가 평범한 수준이라는 의견입니다",                          "low": "마감 처리가 아쉽다는 의견이 있으니 꼼꼼히 확인하세요"},
    "size":      {"high": "사이즈 표기가 정확하고 잘 맞는다는 반응이 많습니다",          "mid": "사이즈가 표기와 약간 차이가 있다는 의견이 있어 참고하세요",          "low": "사이즈 오차가 있다는 의견이 많아 구매 전 실측을 확인하세요"},
    "price":     {"high": "가격 대비 만족도가 높다는 반응이 많습니다",                   "mid": "가격 대비 무난하다는 의견이 많습니다",                              "low": "가격에 비해 아쉽다는 의견이 있습니다"},
    "color":     {"high": "실물 색상이 사진과 비슷하다는 반응이 많습니다",               "mid": "실물 색상이 사진과 약간 차이가 있다는 의견이 있습니다",             "low": "실물 색상이 사진과 다르다는 의견이 많아 참고하세요"},
    "design":    {"high": "디자인이 세련되고 예쁘다는 반응이 많습니다",                  "mid": "디자인이 무난하고 활용도가 높다는 의견입니다",                      "low": "디자인이 기대와 다르다는 의견이 있습니다"},
    "comfort":   {"high": "착용했을 때 편안하다는 반응이 많습니다",                      "mid": "착용감이 무난하다는 의견이 많습니다",                               "low": "착용 시 불편함을 언급한 리뷰가 있으니 참고하세요"},
    "delivery":  {"high": "배송이 빠르고 포장 상태가 좋다는 반응이 많습니다",            "mid": "배송이 보통 수준이라는 의견입니다",                                 "low": "배송 지연이나 포장 불량을 언급한 리뷰가 있습니다"},
    "care":      {"high": "세탁 후에도 형태가 잘 유지된다는 반응이 많습니다",            "mid": "세탁 관리가 크게 어렵지 않다는 의견입니다",                         "low": "세탁 후 변형이나 보풀을 언급한 리뷰가 있으니 주의하세요"},
    "sheerness": {"high": "속이 비치지 않는다는 반응이 많습니다",                        "mid": "얇은 옷 안에 입으면 약간 비칠 수 있다는 의견이 있습니다",           "low": "비침이 있다는 의견이 많아 안에 받쳐 입는 것을 권장합니다"},
    "stretch":   {"high": "신축성이 좋아 활동하기 편하다는 반응이 많습니다",             "mid": "신축성이 보통 수준이라는 의견입니다",                               "low": "신축성이 부족해 활동이 불편할 수 있다는 의견이 있습니다"},
    "season":    {"high": "계절감이 잘 맞아 입기 좋다는 반응이 많습니다",                "mid": "계절을 크게 타지 않아 다양하게 활용 가능하다는 의견입니다",         "low": "계절감이 맞지 않는다는 의견이 있어 구매 전 참고하세요"},
}


def _build_summary(key: str, score: float, clauses: list[str], display_keywords: list[str]) -> str:
    """top display_keyword의 전용 템플릿을 우선 사용하고, 없으면 속성별 폴백을 반환합니다."""
    level = "high" if score >= 0.72 else "mid" if score >= 0.48 else "low"

    kw_counter: Counter[str] = Counter()
    for clause in clauses:
        for kw in display_keywords:
            if kw in clause:
                kw_counter[kw] += 1

    top_kw = kw_counter.most_common(1)[0][0] if kw_counter else None
    if top_kw and top_kw in _KEYWORD_TEMPLATES:
        if top_kw in _DIRECTION_HINTS and level in ("mid", "low"):
            direction_map = _DIRECTION_HINTS[top_kw]
            dir_counter: Counter[str] = Counter()
            for clause in clauses:
                for direction in direction_map:
                    if direction in clause:
                        dir_counter[direction] += 1
            if dir_counter:
                top_dir = dir_counter.most_common(1)[0][0]
                direction_template = direction_map[top_dir].get(level)
                if direction_template:
                    return direction_template
        return _KEYWORD_TEMPLATES[top_kw].get(level, "")

    return _ASPECT_TEMPLATES.get(key, {}).get(level, "")


def analyze_reviews(
    reviews: list[str],
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> tuple[dict[str, float], dict[str, str]]:
    """
    리뷰 목록을 받아 속성별 평균 감성 점수와 대표 문장 요약을 반환합니다.

    on_progress(done, total)이 주어지면 처리된 문장/리뷰 수를 콜백으로 보고합니다.

    Returns:
        scores: {"fit": 0.82, "material": 0.74, ...}
        summaries: {"fit": "핏이 예뻐요 / 오버핏이라 좋아요", ...}
    """
    from analysis.aspects import FASHION_ASPECTS

    analyzer = get_analyzer()

    # 모든 리뷰에서 문장을 한 번에 수집
    all_sentences: list[str] = []
    for review in reviews:
        sentences = [s.strip() for s in re.split(r"[.!?。\n]+", review) if len(s.strip()) >= 4]
        all_sentences.extend(sentences)

    if not all_sentences:
        return {}, {}

    # API 호출은 배치로 한 번에 처리
    if isinstance(analyzer, KlueBertAnalyzer):
        sentence_scores = analyzer.score_sentences(all_sentences, on_progress=on_progress)
    else:
        # PyABSA는 기존 방식 유지
        aggregated: dict[str, list[float]] = {}
        all_snippets: dict[str, list[str]] = {}
        total_reviews = len(reviews)
        for i, review in enumerate(reviews):
            scores, snippets = analyzer.analyze(review)
            for key, score in scores.items():
                aggregated.setdefault(key, []).append(score)
            for key, sents in snippets.items():
                all_snippets.setdefault(key, []).extend(sents)
            if on_progress:
                on_progress(i + 1, total_reviews)
        scores_out = {k: round(sum(v) / len(v), 4) for k, v in aggregated.items()}
        aspect_kw_map = {a.key: a.display_keywords for a in FASHION_ASPECTS}
        summaries = {
            key: _build_summary(key, score, all_snippets.get(key, []), aspect_kw_map.get(key, []))
            for key, score in scores_out.items()
        }
        return scores_out, summaries

    # 문장별 점수를 속성으로 집계
    aggregated_scores: dict[str, list[float]] = {}
    all_snippets: dict[str, list[str]] = {}

    for sent, score in zip(all_sentences, sentence_scores):
        for fa in FASHION_ASPECTS:
            if any(kw in sent for kw in fa.keywords):
                aggregated_scores.setdefault(fa.key, []).append(score)
                all_snippets.setdefault(fa.key, []).append(_extract_relevant_clause(sent, fa.keywords))

    scores_out = {k: round(sum(v) / len(v), 4) for k, v in aggregated_scores.items()}
    aspect_kw_map = {a.key: a.display_keywords for a in FASHION_ASPECTS}
    summaries = {
        key: _build_summary(key, score, all_snippets.get(key, []), aspect_kw_map.get(key, []))
        for key, score in scores_out.items()
    }

    return scores_out, summaries
