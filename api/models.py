from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("source", "product_code", name="uq_source_product_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)        # "ably" | "musinsa"
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    brand: Mapped[str] = mapped_column(String(128), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    analysis: Mapped[list["AnalysisResult"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    body_fit_reviews: Mapped[list["BodyFitReview"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    reviewer: Mapped[str] = mapped_column(String(128), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    size_bought: Mapped[str] = mapped_column(String(64), nullable=True)
    height: Mapped[str] = mapped_column(String(16), nullable=True)
    weight: Mapped[str] = mapped_column(String(16), nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="reviews")


class BodyFitReview(Base):
    """체형 유사 리뷰 추천 전용 데이터. ABSA 분석(Review/AnalysisResult)과는 분리되어 있습니다."""
    __tablename__ = "body_fit_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=True)
    size_bought: Mapped[str] = mapped_column(String(64), nullable=True)
    fit_verdict: Mapped[str] = mapped_column(String(16), nullable=True)  # small | fit | big | unknown
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="body_fit_reviews")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    review_count: Mapped[int] = mapped_column(Integer)
    scores: Mapped[dict] = mapped_column(JSON)
    summaries: Mapped[dict] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="analysis")
