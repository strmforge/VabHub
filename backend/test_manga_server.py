#!/usr/bin/env python3
"""
最小漫画服务器 - 用于测试P1 manga_download_job实现
绕过技术债务问题，只加载manga相关API
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, close_db
from app.core.logging import setup_logging
# 直接导入manga模块，绕过__init__.py的技术债务
from app.api.manga_local import router as manga_local_router
from app.api.manga_remote import router as manga_remote_router
from app.api.manga_progress import router as manga_progress_router
from app.api.manga_sync import router as manga_sync_router
from app.api.manga_follow import router as manga_follow_router
from app.api.reading_hub import router as reading_hub_router
from app.api.auth import router as auth_router
from loguru import logger

# 创建最小FastAPI应用
app = FastAPI(
    title="VabHub Manga Test Server",
    description="最小漫画服务器 - 用于测试manga_download_job实现",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册核心路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(manga_local_router, tags=["本地漫画库"])
app.include_router(manga_remote_router, tags=["远程漫画"])
app.include_router(manga_progress_router, tags=["漫画阅读进度"])
app.include_router(manga_sync_router, tags=["漫画同步"])
app.include_router(manga_follow_router, tags=["漫画追更"])
app.include_router(reading_hub_router, tags=["阅读中心"])

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    setup_logging()
    logger.info("最小漫画服务器启动中...")
    await init_db()
    logger.info("数据库初始化完成")
    logger.info("漫画API已加载，可以测试manga_download_job功能")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    await close_db()
    logger.info("最小漫画服务器已关闭")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "VabHub Manga Test Server",
        "purpose": "测试manga_download_job实现",
        "available_apis": [
            "/api/manga/local/download-jobs/summary",
            "/api/manga/local/download-jobs",
            "/api/manga/local/download-jobs/{id}"
        ]
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "server": "manga-test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
