from datetime import datetime
from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    product_code: str
    name: str
    brand: str | None
    image_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: int
    reviewer: str | None
    rating: int | None
    body: str
    size_bought: str | None
    height: str | None
    weight: str | None
    crawled_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultOut(BaseModel):
    id: int
    product_id: int
    review_count: int
    scores: dict[str, float]
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class CrawlRequest(BaseModel):
    product_code: str
    max_reviews: int = 100


class AnalyzeRequest(BaseModel):
    product_code: str
