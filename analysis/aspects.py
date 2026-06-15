"""패션 리뷰 분석 대상 속성(Aspect) 정의."""

from dataclasses import dataclass, field


@dataclass
class Aspect:
    key: str
    label: str
    keywords: list[str] = field(default_factory=list)
    # 요약에 표시할 완성형 키워드 (detection용 어간과 분리)
    display_keywords: list[str] = field(default_factory=list)


FASHION_ASPECTS: list[Aspect] = [
    Aspect(
        key="fit",
        label="핏",
        keywords=["핏", "핏감", "실루엣", "허리라인", "맞음", "딱 맞", "여유롭", "루즈", "타이트", "오버핏", "슬림핏", "정핏"],
        display_keywords=["오버핏", "슬림핏", "정핏", "루즈핏", "타이트핏", "실루엣"],
    ),
    Aspect(
        key="material",
        label="소재",
        keywords=["소재", "원단", "재질", "순면", "코튼", "울소재", "폴리", "촉감", "부드럽", "까슬", "두께"],
        display_keywords=["순면", "코튼", "울소재", "폴리", "촉감", "두께감"],
    ),
    Aspect(
        key="finish",
        label="마감",
        keywords=["마감", "박음질", "스티칭", "봉제", "바느질", "실밥", "올풀림", "뜯김", "튼튼하게", "조잡", "허술", "내구성", "완성도", "퀄리티", "품질", "정교"],
        display_keywords=["박음질", "봉제", "실밥", "올풀림", "내구성", "퀄리티", "완성도"],
    ),
    Aspect(
        key="size",
        label="사이즈",
        keywords=["사이즈", "치수", "크기", "작게", "크게", "맞는", "사이즈표", "실측", "길이"],
        display_keywords=["사이즈표", "실측", "기장", "어깨너비"],
    ),
    Aspect(
        key="price",
        label="가격",
        keywords=["가격", "가성비", "비싸", "저렴", "합리적", "값어치", "돈값", "싸게"],
        display_keywords=["가성비", "합리적", "값어치", "돈값"],
    ),
    Aspect(
        key="color",
        label="색상",
        keywords=["색상", "색감", "컬러", "색깔", "실제 색", "사진과", "보정", "색톤", "밝기", "선명"],
        display_keywords=["색감", "색톤", "보정", "실제색"],
    ),
    Aspect(
        key="design",
        label="디자인",
        keywords=["디자인", "스타일", "예쁘", "이쁘", "멋있", "세련", "유니크", "패턴", "프린트", "무늬", "모양"],
        display_keywords=["스타일", "패턴", "프린트", "유니크", "무늬"],
    ),
    Aspect(
        key="comfort",
        label="착용감",
        keywords=["착용감", "편안", "편하", "불편", "가볍", "무겁", "숨막", "통기성", "땀나", "보온", "따뜻", "시원"],
        display_keywords=["통기성", "보온성", "착용감", "무게감"],
    ),
    Aspect(
        key="delivery",
        label="배송",
        keywords=["배송", "배달", "도착", "빠르", "느리", "포장", "박스", "훼손", "빠른배송", "배송기간"],
        display_keywords=["포장", "빠른배송", "배송기간", "박스"],
    ),
    Aspect(
        key="care",
        label="관리",
        keywords=["세탁", "빨래", "관리", "줄어", "변형", "탈색", "보풀", "필링", "건조", "다림질"],
        display_keywords=["보풀", "탈색", "필링", "변형", "다림질"],
    ),
    Aspect(
        key="sheerness",
        label="비침",
        keywords=["비침", "비쳐", "비치는", "속보임", "속이 보", "투명", "비춰", "안비침", "비침없"],
        display_keywords=["비침", "속보임", "안비침"],
    ),
    Aspect(
        key="stretch",
        label="신축성",
        keywords=["신축성", "스판", "늘어나", "늘어남", "탄성", "탄력", "쭉쭉", "伸縮", "안늘어", "잘늘어"],
        display_keywords=["스판", "탄성", "탄력"],
    ),
    Aspect(
        key="season",
        label="계절감",
        keywords=["계절", "여름", "겨울", "봄옷", "가을", "사계절", "간절기", "더워", "추워", "시원", "따뜻", "보온"],
        display_keywords=["여름", "겨울", "간절기", "사계절", "봄가을"],
    ),
]

ASPECT_KEYS = [a.key for a in FASHION_ASPECTS]
