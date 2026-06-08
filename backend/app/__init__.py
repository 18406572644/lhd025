from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base
from .routers import (
    auth_router,
    corners_router,
    checkins_router,
    routes_router,
    achievements_router,
    shares_router,
    users_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="城市小众角落探索打卡系统 API",
        description="基于 FastAPI 的异步后端接口，支持角落信息发布、打卡记录、路线规划、用户分享和探索成就",
        version="1.0.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(corners_router, prefix="/api")
    app.include_router(checkins_router, prefix="/api")
    app.include_router(routes_router, prefix="/api")
    app.include_router(achievements_router, prefix="/api")
    app.include_router(shares_router, prefix="/api")
    app.include_router(users_router, prefix="/api")

    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "message": "城市小众角落探索打卡系统 API 运行正常"}

    return app
