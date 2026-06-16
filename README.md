# ReviewLens

패션 쇼핑몰 리뷰 기반 속성 감성 분석(ABSA) 서비스

쇼핑몰 상품 URL 또는 ID를 입력하면 리뷰를 수집하고, 핏·소재·마감 등 13가지 속성별로 감성 점수를 분석합니다.
사용자가 관심 있는 항목을 선택해 개인화된 분석 결과를 확인할 수 있습니다.

## 주요 기능

- **멀티 쇼핑몰 지원** — 에이블리 / 무신사 / 지그재그 / 하이버 URL 붙여넣기로 바로 분석
- **13가지 속성 분석** — 핏, 소재, 마감, 사이즈, 가격, 색상, 디자인, 착용감, 배송, 관리, 비침, 신축성, 계절감
- **키워드별 자연스러운 요약** — 각 속성 툴팁에 키워드 맞춤 문장으로 점수 근거 표시
- **개인화 필터** — 관심 항목만 선택해 레이더/막대 차트에 표시 (localStorage 저장)
- **나만의 종합 점수** — 관심 속성별 중요도(1~5)를 직접 설정하면 가중 평균으로 계산한 개인화 종합 점수 표시
- **전체 평균 비교** — 분석된 상품들의 평균과 현재 상품 점수 비교
- **앱 공유 링크 지원** — 쇼핑몰 앱에서 공유한 onelink/단축 링크도 그대로 붙여넣어 분석 가능
- **HuggingFace Inference API** — `hun3359/klue-bert-base-sentiment` 모델을 HF 서버 GPU에서 배치 추론
- **랜딩 페이지** — 스크롤 진입 애니메이션 포함 서비스 소개 페이지 (채점 방식·점수 예시·사용 방법 등)
- **방문자 추적** — 랜딩 페이지 접속 시 IP·기기·UTM 등을 Google Sheets에 자동 기록 (`visitors_final` 시트)
- **피드백 수집** — 분석 완료 후 의견 제출 페이지, Google Sheets에 별도 기록 (`feedback_final` 시트)

## 프로젝트 구조

```
ReviewLens/
├── crawler/
│   ├── ably.py        # 에이블리 크롤러 (REST API)
│   ├── musinsa.py     # 무신사 크롤러 (REST API)
│   ├── zigzag.py      # 지그재그 크롤러 (GraphQL API)
│   └── hiver.py       # 하이버 크롤러 (Brandi REST API)
├── analysis/
│   ├── aspects.py     # 속성 정의 및 키워드
│   └── absa.py        # ABSA 분석 (HuggingFace Inference API)
├── api/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       └── products.py
├── frontend/          # React + Vite + Tailwind
│   └── src/
│       ├── pages/
│       │   ├── Landing.tsx       # 랜딩 페이지 (/)
│       │   ├── Home.tsx          # 분석 시작 (/app)
│       │   ├── ProductDetail.tsx # 분석 결과 (/products/:source/:code)
│       │   └── Feedback.tsx      # 피드백 폼 (/feedback)
│       ├── components/
│       │   ├── ScoreRadar.tsx
│       │   └── ScoreBars.tsx
│       └── utils/
│           └── tracking.ts       # Google Sheets 방문자·피드백 기록
├── render.yaml        # Render 배포 설정
└── requirements.txt
```

## 실행 방법

### 사전 준비

`.env` 파일을 프로젝트 루트에 생성합니다.

```
ABLY_ANONYMOUS_TOKEN=여기에_토큰_입력
HF_TOKEN=여기에_토큰_입력
```

- **ABLY_ANONYMOUS_TOKEN** — 브라우저에서 `m.a-bly.com` 접속 후 Network 탭 → 아무 API 요청 헤더의 `x-anonymous-token` 값 복사
- **HF_TOKEN** — [HuggingFace](https://huggingface.co/settings/tokens)에서 Read 권한 토큰 발급

### 백엔드

```bash
# 가상환경 생성 및 활성화
python -m venv venv && source venv/bin/activate

# 의존성 설치
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
| GET | `/products/resolve-url` | 앱 공유 링크(onelink/단축 URL)를 실제 상품 URL로 변환 |

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
| 에이블리 | `a-bly.com/goods/{상품ID}` |
| 무신사 | `musinsa.com/products/{상품ID}` |
| 지그재그 | `zigzag.kr/catalog/products/{상품ID}` |
| 하이버 | `hiver.co.kr/products/{상품ID}` |

쇼핑몰 앱의 공유 버튼으로 복사한 링크(onelink, 단축 URL 등)도 그대로 붙여넣으면 자동으로 변환되어 분석됩니다.
- 하이버 onelink는 쿼리 파라미터(`id=`)에서 바로 추출
- 무신사(`onelink.me`)·에이블리(`applink.a-bly.com`)·지그재그(`s.zigzag.kr`) 단축 링크는 백엔드에서 리다이렉트를 추적해 실제 URL로 변환
