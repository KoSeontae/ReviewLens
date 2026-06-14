from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from api.database import get_db
from api.models import Product, Review, AnalysisResult
from api.schemas import ProductOut, ReviewOut, AnalysisResultOut, CrawlRequest, AnalyzeRequest
from analysis.absa import analyze_reviews

router = APIRouter(prefix="/products", tags=["products"])


def _get_crawler(source: str):
    if source == "ably":
        from crawler.ably import crawl_product_reviews
    elif source == "musinsa":
        from crawler.musinsa import crawl_product_reviews
    elif source == "zigzag":
        from crawler.zigzag import crawl_product_reviews
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 쇼핑몰: {source}")
    return crawl_product_reviews


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

    if not product:
        product = Product(
            source=req.source,
            product_code=req.product_code,
            name=raw_reviews[0].product_name,
        )
        db.add(product)
        await db.flush()
    else:
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

    scores = analyze_reviews(review_texts)

    analysis = AnalysisResult(
        product_id=product.id,
        review_count=len(review_texts),
        scores=scores,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
