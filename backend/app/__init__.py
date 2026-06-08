from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
import os
from typing import Optional

from .database import engine, Base, get_db
from .config import get_settings
from .auth import get_current_user
from .routers import (
    auth_router,
    corners_router,
    checkins_router,
    routes_router,
    achievements_router,
    shares_router,
    users_router,
    uploads_router,
)

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


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
    app.include_router(uploads_router, prefix="/api")

    if settings.STORAGE_TYPE == "local":
        os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
        
        if settings.IMAGE_REQUIRE_AUTH:
            @app.get("/uploads/{file_path:path}", include_in_schema=False)
            async def serve_local_image_with_auth(
                file_path: str,
                token: Optional[str] = Depends(oauth2_scheme),
                db = Depends(get_db)
            ):
                full_path = os.path.join(settings.STORAGE_LOCAL_PATH, file_path)
                
                if not os.path.exists(full_path):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="文件不存在"
                    )
                
                if not token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要认证才能访问此图片"
                    )
                
                try:
                    await get_current_user(token=token, db=db)
                except HTTPException:
                    raise
                
                return FileResponse(full_path)
        else:
            app.mount("/uploads", StaticFiles(directory=settings.STORAGE_LOCAL_PATH), name="uploads")

    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "message": "城市小众角落探索打卡系统 API 运行正常"}

    return app
