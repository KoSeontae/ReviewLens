from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.models import Product, Review, AnalysisResult
from api.schemas import ProductOut, ReviewOut, AnalysisResultOut, CrawlRequest, AnalyzeRequest
from crawler.ably import crawl_product_reviews
from analysis.absa import analyze_reviews

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    return result.scalars().all()


@router.get("/{musinsa_id}", response_model=ProductOut)
async def get_product(musinsa_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.musinsa_id == musinsa_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{musinsa_id}/reviews", response_model=list[ReviewOut])
async def get_reviews(musinsa_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.musinsa_id == musinsa_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = await db.execute(select(Review).where(Review.product_id == product.id))
    return reviews.scalars().all()


@router.get("/{musinsa_id}/analysis", response_model=AnalysisResultOut)
async def get_analysis(musinsa_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.musinsa_id == musinsa_id))
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
    """무신사 상품 리뷰를 크롤링해 DB에 저장합니다."""
    # 이미 존재하면 재수집 스킵
    existing = await db.execute(select(Product).where(Product.musinsa_id == req.musinsa_id))
    product = existing.scalar_one_or_none()

    raw_reviews = await crawl_product_reviews(req.musinsa_id, req.max_reviews)
    if not raw_reviews:
        raise HTTPException(status_code=422, detail="No reviews found for this product.")

    if not product:
        product = Product(
            musinsa_id=req.musinsa_id,
            name=raw_reviews[0].product_name,
        )
        db.add(product)
        await db.flush()

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
    result = await db.execute(select(Product).where(Product.musinsa_id == req.musinsa_id))
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
