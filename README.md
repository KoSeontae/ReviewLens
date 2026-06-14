# ReviewLens

에이블리 패션 리뷰 기반 ABSA(속성 감성 분석) 서비스

## 프로젝트 구조

```
ReviewLens/
├── crawler/          # 에이블리 리뷰 수집 (httpx)
│   └── ably.py
├── analysis/         # ABSA 모델 (PyABSA → klue-bert-base-sentiment 폴백)
│   ├── aspects.py    # 속성 정의 (핏, 소재, 마감, 사이즈, 가격)
│   └── absa.py
├── api/              # FastAPI 백엔드
│   ├── main.py
│   ├── models.py     # SQLAlchemy ORM
│   ├── schemas.py    # Pydantic 스키마
│   └── routers/
│       └── products.py
├── frontend/         # React + Vite + Tailwind
└── requirements.txt
```

## 실행 방법

### 백엔드

```bash
# 의존성 설치
python -m venv venv && source venv/bin/activate
pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
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
| POST | `/products/crawl` | 에이블리 상품 리뷰 수집 |
| POST | `/products/analyze` | ABSA 분석 실행 |
| GET | `/products/` | 전체 상품 목록 |
| GET | `/products/{id}` | 상품 상세 |
| GET | `/products/{id}/reviews` | 리뷰 목록 |
| GET | `/products/{id}/analysis` | 분석 결과 |

## 분석 속성

| 키 | 한글 | 키워드 예시 |
|----|------|------------|
| fit | 핏 | 핏감, 실루엣, 루즈, 오버핏 |
| material | 소재 | 원단, 촉감, 두께, 부드럽 |
| finish | 마감 | 박음질, 퀄리티, 내구성 |
| size | 사이즈 | 실측, 크기, 사이즈표 |
| price | 가격 | 가성비, 합리적, 값어치 |
