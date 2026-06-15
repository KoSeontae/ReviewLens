# ReviewLens

패션 쇼핑몰 리뷰 기반 속성 감성 분석(ABSA) 서비스

쇼핑몰 사이트(이블리, 무신사, 지그재그)의 상품 리뷰를 수집하고, 핏·소재·마감 등 13가지 속성별로 감성 점수를 분석합니다.
사용자가 관심 있는 항목을 선택해 개인화된 분석 결과를 확인할 수 있습니다.

## 주요 기능

- **멀티 쇼핑몰 지원** — 에이블리 / 무신사 / 지그재그 URL 붙여넣기로 바로 분석
- **13가지 속성 분석** — 핏, 소재, 마감, 사이즈, 가격, 색상, 디자인, 착용감, 배송, 관리, 비침, 신축성, 계절감
- **개인화 필터** — 관심 항목만 선택해 레이더/막대 차트에 표시 (localStorage 저장)
- **전체 평균 비교** — 분석된 상품들의 평균과 현재 상품 점수 비교
- **리뷰 요약** — 각 속성 툴팁에 점수 근거 문장 표시

## 프로젝트 구조

```
ReviewLens/
├── crawler/
│   ├── ably.py        # 에이블리 크롤러 (REST API)
│   ├── musinsa.py     # 무신사 크롤러 (REST API)
│   └── zigzag.py      # 지그재그 크롤러 (GraphQL API)
├── analysis/
│   ├── aspects.py     # 속성 정의 및 키워드
│   └── absa.py        # ABSA 분석 (klue-bert-base-sentiment)
├── api/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       └── products.py
├── frontend/          # React + Vite + Tailwind
│   └── src/
│       ├── pages/
│       │   ├── Home.tsx
│       │   └── ProductDetail.tsx
│       └── components/
│           ├── ScoreRadar.tsx
│           └── ScoreBars.tsx
├── render.yaml        # Render 배포 설정
└── requirements.txt
```

## 실행 방법

### 사전 준비

`.env` 파일을 프로젝트 루트에 생성하고 에이블리 토큰을 입력합니다.

```
ABLY_ANONYMOUS_TOKEN=여기에_토큰_입력
```

에이블리 토큰은 브라우저에서 `m.a-bly.com` 접속 후 Network 탭 → 아무 API 요청 헤더의 `x-anonymous-token` 값을 복사합니다.

### 백엔드

```bash
# 가상환경 생성 및 활성화
python -m venv venv && source venv/bin/activate

# 의존성 설치 (CPU 전용 torch)
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 서버 실행
venv/bin/uvicorn api.main:app --reload
# → http://localhost:8000
# → API 문서: http://localhost:8000/docs
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/products/crawl` | 리뷰 수집 |
| POST | `/products/analyze` | ABSA 분석 실행 |
| GET | `/products/averages` | 전체 상품 속성별 평균 점수 |
| GET | `/products/` | 전체 상품 목록 |
| GET | `/products/{source}/{code}` | 상품 상세 |
| GET | `/products/{source}/{code}/reviews` | 리뷰 목록 |
| GET | `/products/{source}/{code}/analysis` | 분석 결과 |

## 분석 속성 (13가지)

| 키 | 한글 | 주요 키워드 |
|----|------|------------|
| fit | 핏 | 핏감, 실루엣, 오버핏, 슬림핏 |
| material | 소재 | 원단, 촉감, 두께, 부드럽 |
| finish | 마감 | 박음질, 봉제, 내구성, 퀄리티 |
| size | 사이즈 | 실측, 크기, 사이즈표, 길이 |
| price | 가격 | 가성비, 합리적, 값어치 |
| color | 색상 | 색감, 컬러, 실제 색, 사진과 |
| design | 디자인 | 스타일, 예쁘, 세련, 패턴 |
| comfort | 착용감 | 편안, 편하, 통기성, 보온 |
| delivery | 배송 | 배송, 포장, 도착, 빠르 |
| care | 관리 | 세탁, 보풀, 변형, 탈색 |
| sheerness | 비침 | 비침, 비쳐, 속보임, 투명 |
| stretch | 신축성 | 스판, 탄성, 늘어나, 쭉쭉 |
| season | 계절감 | 여름, 겨울, 간절기, 사계절 |

## 지원 쇼핑몰 URL 형식

| 쇼핑몰 | URL 형식 |
|--------|---------|
| 에이블리 | `m.a-bly.com/goods/{상품ID}` |
| 무신사 | `musinsa.com/products/{상품ID}` |
| 지그재그 | `zigzag.kr/catalog/products/{상품ID}` |
