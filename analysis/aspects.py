"""패션 리뷰 분석 대상 속성(Aspect) 정의."""

from dataclasses import dataclass, field


@dataclass
class Aspect:
    key: str          # 내부 식별자
    label: str        # 화면 표시명
    keywords: list[str] = field(default_factory=list)


FASHION_ASPECTS: list[Aspect] = [
    Aspect(
        key="fit",
        label="핏",
        keywords=["핏", "핏감", "실루엣", "라인", "맞음", "딱", "여유", "루즈", "타이트", "오버핏"],
    ),
    Aspect(
        key="material",
        label="소재",
        keywords=["소재", "원단", "재질", "면", "울", "폴리", "촉감", "부드럽", "까슬", "두께"],
    ),
    Aspect(
        key="finish",
        label="마감",
        keywords=["마감", "박음질", "스티칭", "퀄리티", "품질", "완성도", "내구성", "뜯김", "튼튼", "조잡", "허술", "깔끔", "정교"],
    ),
    Aspect(
        key="size",
        label="사이즈",
        keywords=["사이즈", "치수", "크기", "작게", "크게", "맞는", "사이즈표", "실측", "길이"],
    ),
    Aspect(
        key="price",
        label="가격",
        keywords=["가격", "가성비", "비싸", "싸", "저렴", "합리적", "값어치", "돈값"],
    ),
]

ASPECT_KEYS = [a.key for a in FASHION_ASPECTS]
