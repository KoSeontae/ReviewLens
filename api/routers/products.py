from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from api.database import get_db
from api.models import Product, Review, AnalysisResult, BodyFitReview
from api.schemas import (
    ProductOut, ReviewOut, AnalysisResultOut, CrawlRequest, AnalyzeRequest,
    FitRecommendRequest, FitRecommendationOut,
)
from analysis.absa import analyze_reviews
from analysis.fit_recommender import normalize_fit_label, build_recommendation, FitReview as FitReviewData

router = APIRouter(prefix="/products", tags=["products"])

# 분석 진행률(메모리 캐시). 키: "{source}:{product_code}"
_analysis_progress: dict[str, dict] = {}


def _progress_key(source: str, product_code: str) -> str:
    return f"{source}:{product_code}"


@router.get("/{source}/{product_code}/analyze/progress")
async def get_analyze_progress(source: str, product_code: str):
    """진행 중인 분석의 처리된 문장 수 / 전체 문장 수를 반환합니다."""
    progress = _analysis_progress.get(_progress_key(source, product_code))
    if not progress:
        return {"done": 0, "total": 0, "running": False}
    return progress


@router.get("/resolve-url")
async def resolve_url(url: str):
    """앱 공유 링크(onelink, 단축 URL)를 실제 상품 URL로 변환합니다."""
    import httpx
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            r = await client.get(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            })
            resolved = str(r.url)
            if resolved.startswith("http"):
                return {"url": resolved}
            raise HTTPException(status_code=400, detail="웹 URL로 변환할 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL 변환 실패: {e}")


def _get_crawler(source: str):
    if source == "ably":
        from crawler.ably import crawl_product_reviews
    elif source == "musinsa":
        from crawler.musinsa import crawl_product_reviews
    elif source == "zigzag":
        from crawler.zigzag import crawl_product_reviews
    elif source == "hiver":
        from crawler.hiver import crawl_product_reviews
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 쇼핑몰: {source}")
    return crawl_product_reviews


def _get_fit_crawler(source: str):
    if source == "ably":
        from crawler.ably import crawl_fit_reviews
    elif source == "musinsa":
        from crawler.musinsa import crawl_fit_reviews
    elif source == "zigzag":
        from crawler.zigzag import crawl_fit_reviews
    elif source == "hiver":
        from crawler.hiver import crawl_fit_reviews
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 쇼핑몰: {source}")
    return crawl_fit_reviews


@router.get("/averages", response_model=dict[str, float])
async def get_averages(db: AsyncSession = Depends(get_db)):
    """분석된 모든 상품의 속성별 평균 점수를 반환합니다."""
    result = await db.execute(
        select(AnalysisResult).order_by(AnalysisResult.analyzed_at.desc())
    )
    all_results = result.scalars().all()

    # 상품별 최신 분석 결과만 사용
    seen = set()
    latest = []
    for r in all_results:
        if r.product_id not in seen:
            seen.add(r.product_id)
            latest.append(r)

    if not latest:
        return {}

    aspects = ["fit", "material", "finish", "size", "price"]
    totals: dict[str, list[float]] = {a: [] for a in aspects}
    for r in latest:
        for a in aspects:
            if a in r.scores:
                totals[a].append(r.scores[a])

    return {a: sum(v) / len(v) for a, v in totals.items() if v}


@router.get("/", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    return result.scalars().all()


@router.get("/{source}/{product_code}", response_model=ProductOut)
async def get_product(source: str, product_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.source == source, Product.product_code == product_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{source}/{product_code}/reviews", response_model=list[ReviewOut])
async def get_reviews(source: str, product_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.source == source, Product.product_code == product_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = await db.execute(select(Review).where(Review.product_id == product.id))
    return reviews.scalars().all()


@router.get("/{source}/{product_code}/analysis", response_model=AnalysisResultOut)
async def get_analysis(source: str, product_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.source == source, Product.product_code == product_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    analysis = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.product_id == product.id)
        .order_by(AnalysisResult.analyzed_at.desc())
    )
    row = analysis.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found. Run /analyze first.")
    return row


@router.post("/crawl", response_model=ProductOut, status_code=201)
async def crawl_product(req: CrawlRequest, db: AsyncSession = Depends(get_db)):
    """에이블리 또는 무신사 상품 리뷰를 크롤링해 DB에 저장합니다."""
    crawl = _get_crawler(req.source)

    existing = await db.execute(
        select(Product).where(Product.source == req.source, Product.product_code == req.product_code)
    )
    product = existing.scalar_one_or_none()

    raw_reviews = await crawl(req.product_code, req.max_reviews)
    if not raw_reviews:
        raise HTTPException(status_code=422, detail="No reviews found for this product.")

    image_url = raw_reviews[0].image_url if hasattr(raw_reviews[0], "image_url") else None

    if not product:
        product = Product(
            source=req.source,
            product_code=req.product_code,
            name=raw_reviews[0].product_name,
            image_url=image_url,
        )
        db.add(product)
        await db.flush()
    else:
        product.name = raw_reviews[0].product_name
        product.image_url = image_url
        await db.execute(delete(Review).where(Review.product_id == product.id))
        await db.execute(delete(AnalysisResult).where(AnalysisResult.product_id == product.id))

    for r in raw_reviews:
        db.add(Review(
            product_id=product.id,
            reviewer=r.reviewer,
            rating=r.rating,
            body=r.body,
            size_bought=r.size_bought,
            height=r.height,
            weight=r.weight,
        ))

    await db.commit()
    await db.refresh(product)
    return product


@router.post("/{source}/{product_code}/fit-recommendation", response_model=FitRecommendationOut)
async def fit_recommendation(
    source: str,
    product_code: str,
    req: FitRecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    """입력한 키/몸무게와 비슷한 체형의 리뷰를 모아 사이즈·핏 만족도를 추천합니다."""
    result = await db.execute(
        select(Product).where(Product.source == source, Product.product_code == product_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found. Crawl first.")

    existing = await db.execute(select(BodyFitReview).where(BodyFitReview.product_id == product.id))
    rows = existing.scalars().all()

    if not rows:
        crawl_fit = _get_fit_crawler(source)
        raw_fit_reviews = await crawl_fit(product_code, 200)
        for r in raw_fit_reviews:
            db.add(BodyFitReview(
                product_id=product.id,
                height=r.height,
                weight=r.weight,
                size_bought=r.size_bought,
                fit_verdict=normalize_fit_label(source, r.fit_raw_label),
            ))
        await db.commit()
        existing = await db.execute(select(BodyFitReview).where(BodyFitReview.product_id == product.id))
        rows = existing.scalars().all()

    fit_reviews = [
        FitReviewData(
            height=r.height,
            weight=r.weight,
            size_bought=r.size_bought,
            fit_verdict=r.fit_verdict or "unknown",
        )
        for r in rows
    ]
    return build_recommendation(fit_reviews, req.height, req.weight)


@router.post("/analyze", response_model=AnalysisResultOut, status_code=201)
async def analyze_product(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """저장된 리뷰에 ABSA를 실행하고 결과를 반환합니다."""
    result = await db.execute(
        select(Product).where(Product.source == req.source, Product.product_code == req.product_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found. Crawl first.")

    reviews_q = await db.execute(select(Review).where(Review.product_id == product.id))
    review_texts = [r.body for r in reviews_q.scalars().all()]
    if not review_texts:
        raise HTTPException(status_code=422, detail="No reviews to analyze.")

    key = _progress_key(req.source, req.product_code)
    _analysis_progress[key] = {"done": 0, "total": 0, "running": True}

    def on_progress(done: int, total: int) -> None:
        _analysis_progress[key] = {"done": done, "total": total, "running": True}

    try:
        # HF API 호출이 동기/블로킹이라 쓰레드풀에서 실행해 이벤트 루프(진행률 polling)를 막지 않음
        scores, summaries = await run_in_threadpool(analyze_reviews, review_texts, on_progress)
    finally:
        _analysis_progress.pop(key, None)

    analysis = AnalysisResult(
        product_id=product.id,
        review_count=len(review_texts),
        scores=scores,
        summaries=summaries,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
