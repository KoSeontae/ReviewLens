import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import init_db
from api.routers.products import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ReviewLens API",
    description="패션 쇼핑몰 리뷰 기반 속성 감성 분석 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
