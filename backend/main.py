"""
VabHub 后端主应用
基于FastAPI的现代化媒体管理平台
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db, close_db, AsyncSessionLocal
from app.core.logging import setup_logging
from app.core.cache import get_cache
from app.core.middleware import RequestLoggingMiddleware, PerformanceMonitoringMiddleware, ErrorHandlingMiddleware
from app.core.health import get_health_checker
from app.core.scheduler import get_scheduler
from app.core.exceptions import VabHubException
from app.api import api_router
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema as graphql_schema
from app.modules.short_drama.schema_utils import ensure_short_drama_columns
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    
    # 初始化实时日志中心
    try:
        from app.core.log_handler import setup_realtime_logging
        setup_realtime_logging()
        logger.info("实时日志中心已初始化")
    except Exception as e:
        logger.warning(f"实时日志中心初始化失败（不影响启动）: {e}")
    
    await init_db()
    try:
        await ensure_short_drama_columns()
    except Exception as e:
        logger.warning(f"短剧表结构检查失败（不影响启动）: {e}")
    
    # 初始化DNS over HTTPS (DOH)
    try:
        from app.utils.doh import enable_doh
        enable_doh(settings.DOH_ENABLE)
        if settings.DOH_ENABLE:
            logger.info(f"DNS over HTTPS已启用，域名列表: {settings.DOH_DOMAINS}")
        else:
            logger.info("DNS over HTTPS未启用")
    except Exception as e:
        logger.warning(f"DOH初始化失败（不影响启动）: {e}")
    
    # 初始化缓存系统
    cache = get_cache()
    logger.info("缓存系统已初始化")
    
    # 初始化密钥管理器（自动生成随机密钥）
    try:
        from app.core.secret_manager import initialize_secrets
        initialize_secrets()
        logger.info("密钥管理器已初始化（所有密钥已生成或加载）")
    except Exception as e:
        logger.warning(f"密钥管理器初始化失败（不影响启动）: {e}")
    
    # 启动WebSocket后台任务
    try:
        from app.api.websocket import start_websocket_tasks
        await start_websocket_tasks()
        logger.info("WebSocket后台任务已启动")
    except Exception as e:
        logger.warning(f"WebSocket后台任务启动失败（不影响启动）: {e}")
    
    # 初始化API密钥管理器（自动初始化默认密钥）
    try:
        from app.core.api_key_manager import get_api_key_manager
        api_key_manager = get_api_key_manager()
        api_key_manager.initialize_default_keys()
        logger.info("API密钥管理器已初始化（默认密钥已加密存储）")
    except Exception as e:
        logger.warning(f"API密钥管理器初始化失败（不影响启动）: {e}")
    
    # 初始化健康检查器
    health_checker = get_health_checker()
    logger.info("健康检查系统已初始化")
    
    # 启动定时任务调度器
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("定时任务调度器已启动")
    
    # 加载 Local Intel 站点配置
    try:
        from app.core.intel_local.site_profiles import get_site_profile_loader
        from app.core.intel_local.factory import register_site_http_clients
        if settings.INTEL_ENABLED:
            loader = get_site_profile_loader()
            profiles = loader.load_all()
            logger.info(f"LocalIntel 站点配置已加载: {len(profiles)} 个站点")
            
            # 注册 HTTP 客户端（Phase 4）
            try:
                await register_site_http_clients()
            except Exception as e:
                logger.warning(f"LocalIntel HTTP 客户端注册失败（不影响启动）: {e}")
        else:
            logger.debug("LocalIntel 未启用，跳过站点配置加载")
    except Exception as e:
        logger.warning(f"LocalIntel 站点配置加载失败（不影响启动）: {e}")

    # 构建 Local Intel 引擎
    if settings.INTEL_ENABLED:
        try:
            from app.core.intel_local.factory import build_local_intel_engine

            app.state.local_intel_engine = build_local_intel_engine()
            logger.info("LocalIntel 引擎已初始化")
        except Exception as e:
            logger.warning(f"LocalIntel 引擎初始化失败（不影响启动）: {e}")
    
    # 初始化外部索引桥接
    if settings.EXTERNAL_INDEXER_ENABLED and settings.EXTERNAL_INDEXER_MODULE:
        try:
            from app.core.ext_indexer.runtime import DynamicModuleRuntime
            from app.core.ext_indexer.registry import set_runtime, set_auth_bridge
            from app.core.ext_indexer.auth_bridge import NoopExternalAuthBridge
            
            runtime = DynamicModuleRuntime(settings.EXTERNAL_INDEXER_MODULE)
            if runtime.is_loaded:
                set_runtime(runtime)
                set_auth_bridge(NoopExternalAuthBridge())
                app.state.external_indexer_runtime = runtime
                app.state.external_indexer_auth_bridge = NoopExternalAuthBridge()
                logger.info(f"外部索引桥接已初始化: {settings.EXTERNAL_INDEXER_MODULE}")
            else:
                logger.warning("外部索引模块加载失败，外部索引功能将被禁用")
        except Exception as e:
            logger.warning(f"外部索引桥接初始化失败（不影响启动）: {e}")
    else:
        logger.debug("外部索引桥接未启用或未配置模块路径")
    
    # 同步RSSHub配置到数据库
    try:
        from app.modules.rsshub.config_loader import RSSHubConfigLoader
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            config_loader = RSSHubConfigLoader()
            stats = await config_loader.sync_all_to_db(db)
            logger.info(f"RSSHub配置已同步到数据库: {stats}")
    except Exception as e:
        logger.warning(f"RSSHub配置同步失败（不影响启动）: {e}")
    
    # 检查并执行自动更新（如果启用）
    try:
        from app.modules.system.update_manager import UpdateManager, UpdateMode
        from app.modules.settings.service import SettingsService
        from app.core.database import AsyncSessionLocal
        
        # 从数据库读取更新模式配置
        async with AsyncSessionLocal() as db:
            settings_service = SettingsService(db)
            update_mode_value = await settings_service.get_setting("system_auto_update_mode", category="system")
            auto_update_enabled = await settings_service.get_setting("system_auto_update_enabled", category="system", default=False)
            
            if update_mode_value and update_mode_value != "never" and auto_update_enabled:
                update_manager = UpdateManager()
                try:
                    update_manager.update_mode = UpdateMode(update_mode_value)
                    update_manager.auto_update_enabled = auto_update_enabled
                except ValueError:
                    logger.warning(f"无效的更新模式: {update_mode_value}，使用默认值never")
                    update_manager.update_mode = UpdateMode.NEVER
                
                if update_manager.update_mode != UpdateMode.NEVER:
                    logger.info(f"检测到自动更新模式: {update_manager.update_mode.value}，开始检查更新...")
                    
                    # 在后台任务中执行更新（不阻塞启动）
                    async def auto_update_task():
                        try:
                            # 先检查是否有更新
                            update_info = await update_manager.check_update_available()
                            if update_info.get("has_update"):
                                logger.info("检测到可用更新，开始自动更新...")
                                result = await update_manager.update_system()
                                if result.get("success"):
                                    logger.info(f"自动更新成功: {result.get('message')}")
                                    logger.warning("系统已更新，建议重启以应用更改")
                                else:
                                    logger.debug(f"自动更新检查: {result.get('message')}")
                            else:
                                logger.debug("已是最新版本，无需更新")
                        except Exception as e:
                            logger.error(f"自动更新失败: {e}")
                    
                    # 延迟执行，避免阻塞启动（等待5秒后执行）
                    import asyncio
                    await asyncio.sleep(5)
                    asyncio.create_task(auto_update_task())
    except Exception as e:
        logger.warning(f"自动更新检查失败（不影响启动）: {e}")
    
    # 初始化远程插件事件分发器 (PLUGIN-REMOTE-1)
    try:
        from app.plugin_sdk.events import get_event_bus
        from app.services.remote_plugin_dispatcher import get_remote_dispatcher
        
        event_bus = get_event_bus()
        remote_dispatcher = await get_remote_dispatcher(event_bus)
        app.state.remote_dispatcher = remote_dispatcher
        logger.info("远程插件事件分发器已初始化")
    except Exception as e:
        logger.warning(f"远程插件事件分发器初始化失败（不影响启动）: {e}")
    
    yield
    
    # 关闭时执行
    # 关闭远程插件事件分发器 (PLUGIN-REMOTE-1)
    try:
        from app.services.remote_plugin_dispatcher import shutdown_remote_dispatcher
        await shutdown_remote_dispatcher()
        logger.info("远程插件事件分发器已关闭")
    except Exception as e:
        logger.warning(f"远程插件事件分发器关闭失败（不影响关闭）: {e}")
    
    await scheduler.stop()
    await cache.close()
    await close_db()
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="VabHub API",
    description="新一代智能媒体管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置中间件（按顺序添加）
# 1. 错误处理（最外层）
app.add_middleware(ErrorHandlingMiddleware)

# 2. 性能监控（增强版，支持详细统计）
# 注意：由于FastAPI中间件的初始化方式，我们需要在中间件内部存储实例
# 这里先添加中间件，然后在lifespan中获取实例
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=1.0)

# 3. 请求日志
app.add_middleware(RequestLoggingMiddleware)

# 4. CORS（最内层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL Context
async def get_graphql_context():
    return {"session_factory": AsyncSessionLocal}


# 注册API / GraphQL 路由
# 注意：漫画路由器已经包含了完整的前缀（如/api/manga/...），所以这里使用全局API前缀
api_prefix = getattr(settings, "API_PREFIX", "") or ""
app.include_router(api_router, prefix=api_prefix)
graphql_app = GraphQLRouter(graphql_schema, context_getter=get_graphql_context)
app.include_router(graphql_app, prefix="/graphql")

# 静态文件服务
# 静态文件目录
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 资源文件目录（站点Logo等）
resources_dir = Path(__file__).parent.parent / "resources"
if resources_dir.exists():
    # 映射 /static/assets 到 resources 目录
    assets_dir = resources_dir
    if assets_dir.exists():
        app.mount("/static/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info(f"资源文件目录已挂载: {assets_dir}")

# 媒体文件目录（漫画、电子书等）
from app.core.config import settings
# 漫画文件存储在 COMIC_LIBRARY_ROOT，需要挂载其父目录以便访问 manga/ 子目录
comic_root = Path(getattr(settings, 'COMIC_LIBRARY_ROOT', './data/library/comics'))
# 挂载 data 目录，这样 /media/manga/... 可以访问
media_root = comic_root.parent.parent if comic_root.parent.name == 'comics' else Path('./data')
if media_root.exists():
    app.mount("/media", StaticFiles(directory=str(media_root)), name="media")
    logger.info(f"媒体文件目录已挂载: {media_root}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "VabHub",
        "version": "1.0.0",
        "description": "新一代智能媒体管理平台",
        "docs": "/docs",
        "api": f"{settings.API_PREFIX}"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    health_checker = get_health_checker()
    result = await health_checker.check_all()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/healthz")
async def healthz():
    """
    健康检查端点（Kubernetes兼容）
    
    返回200状态码表示健康，503表示不健康
    """
    health_checker = get_health_checker()
    result = await health_checker.check_all()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/metrics")
async def metrics():
    """
    系统指标端点（Prometheus兼容）
    
    返回Prometheus格式的指标数据
    """
    try:
        from app.core.performance import get_performance_monitor
        monitor = get_performance_monitor()
        metrics_data = await monitor.get_metrics_prometheus()
        return JSONResponse(content=metrics_data, media_type="text/plain")
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@app.get("/health/{check_name}")
async def health_check_item(check_name: str):
    """单项健康检查"""
    health_checker = get_health_checker()
    result = await health_checker.check(check_name)
    if result is None:
        return JSONResponse(
            content={"error": f"健康检查项不存在: {check_name}"},
            status_code=404
        )
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.exception_handler(VabHubException)
async def vabhub_exception_handler(request: Request, exc: VabHubException):
    """VabHub异常处理（统一响应格式）"""
    logger.error(
        f"VabHub异常: {request.method} {request.url.path} - {exc.error_code}: {exc.error_message}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_code": exc.error_code,
            "error_message": exc.error_message,
            "status_code": exc.status_code
        }
    )
    
    # VabHubException的detail可能已经是统一响应格式
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    else:
        # 返回统一响应格式
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "error_message": exc.error_message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat()
            }
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理（统一响应格式）"""
    logger.warning(
        f"请求验证错误: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "errors": exc.errors()
        }
    )
    
    # 格式化验证错误
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "unknown")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "请求参数验证失败",
            "details": {
                "errors": error_details
            },
            "timestamp": datetime.now().isoformat()
        }
    )


# HTTPException由中间件处理，这里不需要重复处理
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     """HTTP异常处理（统一响应格式）"""
#     # 此处理器已被中间件ErrorHandlingMiddleware处理，保留注释以避免冲突
#     pass


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理（统一响应格式）"""
    logger.error(
        f"未处理的异常: {request.method} {request.url.path} - {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error": str(exc),
            "error_type": type(exc).__name__
        }
    )
    
    is_debug = settings.DEBUG
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": str(exc) if is_debug else "内部服务器错误，请稍后重试",
            "details": {
                "error_type": type(exc).__name__
            } if is_debug else {},
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS
    )

