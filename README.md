# ReviewLens

패션 쇼핑몰 리뷰 기반 속성 감성 분석(ABSA) 서비스

쇼핑몰 상품 URL 또는 앱 공유 링크를 입력하면 리뷰를 자동 수집하고, 핏·소재·마감 등 13가지 속성별로 감성 점수를 분석합니다.
사용자가 관심 있는 항목을 선택하고 속성별 중요도를 직접 설정해 개인화된 분석 결과를 확인할 수 있습니다.

## 주요 기능

- **멀티 쇼핑몰 지원** — 에이블리 / 무신사 / 지그재그 / 하이버 URL 붙여넣기로 바로 분석
- **13가지 속성 분석** — 핏, 소재, 마감, 사이즈, 가격, 색상, 디자인, 착용감, 배송, 관리, 비침, 신축성, 계절감
- **키워드별 자연스러운 요약** — 각 속성 툴팁에 키워드 맞춤 문장으로 점수 근거 표시
- **개인화 필터** — 관심 항목만 선택해 레이더/막대 차트에 표시 (localStorage 저장)
- **나만의 종합 점수** — 관심 속성별 중요도(1~5)를 직접 설정하면 가중 평균으로 계산한 개인화 종합 점수 표시
- **전체 평균 비교** — 분석된 상품들의 평균과 현재 상품 점수 비교
- **앱 공유 링크 지원** — 쇼핑몰 앱에서 공유한 onelink/단축 링크도 그대로 붙여넣어 분석 가능
- **체형 유사 리뷰 추천** — 키/몸무게를 입력하면 비슷한 체형의 구매자가 고른 사이즈와 핏 만족도("작아요/잘 맞아요/커요")를 비율로 추천 (ABSA 13속성 분석과 완전히 분리된 별도 기능)
- **분석 진행률 표시** — 리뷰 분석은 시간이 걸릴 수 있어, 처리된 문장 수 / 전체 문장 수를 실시간 진행률 바로 표시
- **HuggingFace Inference API** — `hun3359/klue-bert-base-sentiment` 모델을 HF 서버 GPU에서 배치 추론
- **랜딩 페이지** — 스크롤 진입 애니메이션 포함 서비스 소개 페이지 (채점 방식·점수 예시·사용 방법 등)
- **방문자 추적** — 랜딩 페이지 접속 시 IP·기기·UTM 등을 Google Sheets에 자동 기록 (`visitors_final` 시트)
- **피드백 수집** — 분석 완료 후 의견 제출 페이지에서 의견(선택)과 "구매 결정에 도움이 될 것 같은지"(필수, 예/아니오)를 수집해 Google Sheets에 기록 (`feedback_final` 시트)
- **XyZ 가설 검증** — 수집된 피드백 데이터로 Exact Binomial Test를 실행해 "방문자 중 적어도 X%는 Z를 할 것이다" 형태의 가설을 통계적으로 검증

## 프로젝트 구조

```
ReviewLens/
├── crawler/
│   ├── ably.py             # 에이블리 크롤러 (REST API)
│   ├── musinsa.py          # 무신사 크롤러 (REST API)
│   ├── zigzag.py           # 지그재그 크롤러 (GraphQL API)
│   └── hiver.py            # 하이버 크롤러 (Brandi REST API)
├── analysis/
│   ├── aspects.py          # 속성 정의 및 키워드
│   ├── absa.py             # ABSA 분석 (HuggingFace Inference API, 진행률 콜백 지원)
│   ├── fit_recommender.py  # 체형 유사 리뷰 추천 (ABSA와 분리된 별도 로직)
│   └── hypothesis_test.py  # XyZ 가설 검증 (Exact Binomial Test)
├── api/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       └── products.py     # 크롤링/분석/조회 + 분석 진행률 polling 엔드포인트
├── frontend/                # React + Vite + Tailwind
│   └── src/
│       ├── pages/
│       │   ├── Landing.tsx       # 랜딩 페이지 (/)
│       │   ├── Home.tsx          # 분석 시작 (/app)
│       │   ├── ProductDetail.tsx # 분석 결과 + 진행률 표시 (/products/:source/:code)
│       │   └── Feedback.tsx      # 피드백 폼 (구매 도움 여부 + 의견) (/feedback)
│       ├── components/
│       │   ├── ScoreRadar.tsx
│       │   └── ScoreBars.tsx
│       └── utils/
│           └── tracking.ts       # Google Sheets 방문자·피드백 기록
├── reviewlens.db        # 로컬 SQLite DB (개발용)
├── render.yaml          # Render 배포 설정 (백엔드)
├── netlify.toml          # Netlify 배포 설정 (프론트엔드)
├── requirements.txt
├── .env.example          # 필요한 환경변수 템플릿
└── .python-version       # 권장 Python 버전 (3.11.9)
```

## 실행 방법

### 0. 사전 요구사항

- **Python 3.11.x** (`.python-version` 참고. `pyenv`를 쓰면 `pyenv install 3.11.9` 후 자동 인식)
- **Node.js 20.x** 이상 (`netlify.toml`에서 지정)
- **ABLY_ANONYMOUS_TOKEN**, **HF_TOKEN** 발급 (아래 1단계 참고)

### 1. 환경변수 설정

프로젝트 루트의 `.env.example`을 복사해 `.env` 파일을 만듭니다.

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 항목을 채웁니다.

```
DATABASE_URL=sqlite+aiosqlite:///./reviewlens.db
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
ABLY_ANONYMOUS_TOKEN=여기에_토큰_입력
HF_TOKEN=여기에_토큰_입력
```

| 변수 | 설명 | 발급 방법 |
|------|------|-----------|
| `DATABASE_URL` | DB 접속 문자열 | 로컬 개발은 기본값(SQLite) 그대로 사용. 배포 시 PostgreSQL 등으로 교체 |
| `CORS_ORIGINS` | 허용할 프론트엔드 origin | 로컬 개발은 `http://localhost:5173` |
| `LOG_LEVEL` | 로그 레벨 | 기본값 `INFO` 사용 |
| `ABLY_ANONYMOUS_TOKEN` | 에이블리 리뷰 크롤링용 토큰 | 브라우저에서 `m.a-bly.com` 접속 → 개발자 도구 Network 탭 → 아무 API 요청의 요청 헤더에서 `x-anonymous-token` 값 복사 |
| `HF_TOKEN` | HuggingFace Inference API 토큰 | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)에서 **Read** 권한 토큰 발급 |

> `ABLY_ANONYMOUS_TOKEN`이 없으면 에이블리 외 쇼핑몰(무신사/지그재그/하이버) 분석은 정상 동작합니다. `HF_TOKEN`은 ABSA 분석(`/products/analyze`) 자체에 필수입니다.

### 2. 백엔드 실행

```bash
# 프로젝트 루트에서 가상환경 생성 및 활성화
python3.11 -m venv venv
source venv/bin/activate        # Windows는 venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (.env는 자동으로 로드됩니다)
uvicorn api.main:app --reload
```

- API 서버: http://localhost:8000
- API 문서(Swagger UI): http://localhost:8000/docs — 여기서 각 엔드포인트를 직접 호출해 테스트할 수 있습니다.
- 최초 실행 시 SQLite DB(`reviewlens.db`)와 테이블이 자동 생성됩니다.

### 3. 프론트엔드 실행

새 터미널을 열어 진행합니다.

```bash
cd frontend
npm install
npm run dev
```

- 프론트엔드: http://localhost:5173
- 백엔드 API 주소를 바꿔야 한다면 `frontend/.env`에 `VITE_API_URL=http://localhost:8000` 형태로 지정합니다 (기본값이 `http://localhost:8000`이므로 로컬 실행 시에는 별도 설정이 필요 없습니다).

### 4. 동작 확인 (전체 시나리오)

1. 브라우저에서 http://localhost:5173 접속 → 랜딩 페이지 확인
2. "분석 시작" 또는 `/app`으로 이동 → 쇼핑몰 상품 URL(예: 무신사 상품 링크) 또는 앱 공유 링크 붙여넣기
3. 리뷰 크롤링이 완료되면 상품 상세 페이지(`/products/{source}/{code}`)로 이동
4. "AI 분석 시작" 클릭 → 처리된 문장 수 진행률 바가 표시되며 분석 진행 (시간이 걸릴 수 있음)
5. 분석 완료 후 13가지 속성별 점수를 레이더/막대 차트로 확인, 관심 속성 선택 및 중요도(1~5) 설정 → 개인화된 종합 점수 확인
6. "내 체형과 비슷한 리뷰 추천" 카드에 키/몸무게 입력 → "추천 보기" 클릭 → 비슷한 체형 구매자들의 사이즈·핏 만족도 비율 확인
7. "의견 남기기"로 이동해 "구매 결정에 도움이 될 것 같나요?" 응답(필수) + 의견(선택) 제출

> **참고: "전체 평균 비교" 점수에 대하여**
> `/products/averages`가 보여주는 평균 점수는 그동안 DB에 쌓인 모든 분석 결과를 집계한 값입니다. `*.db` 파일은 `.gitignore`에 포함되어 있어 깃허브에는 올라가지 않으므로, 레포를 새로 클론해 로컬에서 처음 실행하면 DB가 비어 있는 상태로 시작합니다. 이 경우 아직 분석된 상품이 하나도 없어 평균 비교 영역이 비어 있거나 0으로 표시되는 것이 정상이며, **여러 상품을 크롤링·분석할수록 평균 점수가 정상적으로 채워집니다.** 따라서 이 기능을 제대로 확인하려면 2개 이상의 다른 상품에 대해 3~4단계(크롤링 → 분석)를 반복해보는 것을 권장합니다.

### 5. XyZ 가설 검증 스크립트 실행 (선택)

홍보를 통해 피드백 응답이 쌓인 뒤, Google Sheets의 `feedback_final` 시트에서 `purchase_help` 열의 `yes`/`no` 개수를 집계해 아래 명령으로 Exact Binomial Test를 실행합니다.

```bash
python -m analysis.hypothesis_test --yes <예 응답수> --total <전체 응답수> --x 0.15
```

`--x`는 검증하려는 가설의 임계 비율(예: 15%인 경우 `0.15`)입니다. 실행하면 표본 비율, p-value, 95% 신뢰구간과 함께 가설 채택/기각 결론이 출력됩니다.

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/products/crawl` | 리뷰 수집 |
| POST | `/products/analyze` | ABSA 분석 실행 (완료까지 응답을 기다리는 동안 진행률 polling 가능) |
| GET | `/products/{source}/{product_code}/analyze/progress` | 진행 중인 분석의 처리된 문장 수 / 전체 문장 수 조회 |
| GET | `/products/averages` | 전체 상품 속성별 평균 점수 (DB에 분석된 상품이 없으면 빈 값 반환) |
| GET | `/products/` | 전체 상품 목록 |
| GET | `/products/{source}/{code}` | 상품 상세 |
| GET | `/products/{source}/{code}/reviews` | 리뷰 목록 |
| GET | `/products/{source}/{code}/analysis` | 분석 결과 |
| GET | `/products/resolve-url` | 앱 공유 링크(onelink/단축 URL)를 실제 상품 URL로 변환 |
| POST | `/products/{source}/{code}/fit-recommendation` | 키/몸무게를 입력받아 체형 유사 리뷰의 사이즈·핏 만족도 비율 추천 (최초 호출 시 핏 데이터 수집 후 DB에 캐시) |

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

## 체형 유사 리뷰 추천 — 쇼핑몰별 핏 신호 출처

각 쇼핑몰이 리뷰 작성 시 받는 "사이즈가 어땠는지" 설문/평가 데이터를 `analysis/fit_recommender.py`가 `small`/`fit`/`big` 3단계로 정규화합니다. ABSA 13속성 분석에는 사용되지 않는 별도 데이터(`BodyFitReview` 테이블)입니다.

| 쇼핑몰 | 원본 필드 | 예시 값 |
|--------|-----------|---------|
| 무신사 | `reviewSurveySatisfaction.questions` ("사이즈" 항목) | `"정사이즈"`, `"조금 작음"` |
| 에이블리 | `size_rate` (0~4, 2가 정사이즈로 추정) | `2`, `3` |
| 지그재그 | `attribute_list` (category: "사이즈") | `"FIT"`, `"SMALL"`, `"BIG"` |
| 하이버 | `evaluation.wearing_sensation` | `"잘 맞아요"` |

