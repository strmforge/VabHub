"""
搜索相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.search.service import SearchService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class SearchRequest(BaseModel):
    """搜索请求"""
    query: Optional[str] = None  # 搜索关键词
    # 媒体ID搜索
    tmdb_id: Optional[int] = None  # TMDB ID
    imdb_id: Optional[str] = None  # IMDB ID (格式: tt1234567)
    douban_id: Optional[str] = None  # 豆瓣ID
    # 基础筛选
    media_type: Optional[str] = None  # movie, tv, anime
    year: Optional[int] = None
    quality: Optional[str] = None  # 4K, 1080p, 720p
    resolution: Optional[str] = None  # 2160p, 1080p, 720p
    min_size: Optional[float] = None  # GB
    max_size: Optional[float] = None  # GB
    min_seeders: Optional[int] = None
    max_seeders: Optional[int] = None
    include: Optional[str] = None  # 必须包含的关键词
    exclude: Optional[str] = None  # 必须排除的关键词
    sites: Optional[List[str]] = None  # 指定搜索的站点
    # 多维度筛选
    language: Optional[str] = None  # 语言
    category: Optional[str] = None  # 资源分类
    encoding: Optional[str] = None  # 编码格式 (H.264, H.265, etc.)
    source: Optional[str] = None  # 来源 (BluRay, WEB-DL, etc.)
    # 排序和分页
    sort_by: Optional[str] = "seeders"  # seeders, size, date
    sort_order: Optional[str] = "desc"  # asc, desc
    page: Optional[int] = 1
    page_size: Optional[int] = 50
    # 分组选项
    group_by: Optional[str] = None  # site, quality, resolution, category


class SearchResult(BaseModel):
    """搜索结果"""
    title: str
    site: str
    magnet_link: Optional[str] = None
    torrent_url: Optional[str] = None
    size_gb: float
    seeders: int
    leechers: int
    resolution: Optional[str] = None
    quality: Optional[str] = None
    upload_date: Optional[datetime] = None
    category: Optional[str] = None  # 资源分类
    language: Optional[str] = None  # 语言
    encoding: Optional[str] = None  # 编码格式
    source: Optional[str] = None  # 来源
    # 媒体信息（如果通过ID搜索）
    media_info: Optional[dict] = None  # 包含TMDB/IMDB信息


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
    # 分组信息
    grouped_results: Optional[dict] = None  # 如果使用分组，返回分组后的结果
    # 媒体信息（如果通过ID搜索）
    media_info: Optional[dict] = None


@router.post("/", response_model=BaseResponse)
async def search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    执行搜索（支持媒体ID搜索、多维度筛选、智能分组）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": {
            "items": [SearchResult, ...],
            "total": 100,
            "page": 1,
            "page_size": 50,
            "total_pages": 2,
            "grouped_results": {...},  # 如果使用分组
            "media_info": {...}  # 如果通过ID搜索
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 验证搜索参数
        if not request.query and not request.tmdb_id and not request.imdb_id and not request.douban_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_REQUEST",
                    error_message="必须提供搜索关键词或媒体ID（TMDB/IMDB/豆瓣）"
                ).model_dump()
            )
        
        # Phase 9: 优先使用 IndexedSearchService（如果启用 Local Intel）
        from app.core.config import settings
        from app.modules.search.indexed_search_service import IndexedSearchService
        from app.schemas.search import SearchQuery as IndexedSearchQuery
        
        service = SearchService(db)
        indexed_service = None
        
        if settings.INTEL_ENABLED:
            try:
                indexed_service = IndexedSearchService(db, fallback_service=service)
            except Exception as e:
                logger.warning(f"初始化 IndexedSearchService 失败，使用回退服务: {e}")
        
        # 如果通过媒体ID搜索，先获取媒体信息
        media_info = None
        search_query = request.query
        
        if request.tmdb_id or request.imdb_id or request.douban_id:
            media_info = await service.get_media_info_by_id(
                tmdb_id=request.tmdb_id,
                imdb_id=request.imdb_id,
                douban_id=request.douban_id,
                media_type=request.media_type
            )
            if media_info:
                # 使用媒体信息构建搜索关键词
                search_query = media_info.get("title") or search_query
                if not request.media_type and media_info.get("media_type"):
                    request.media_type = media_info.get("media_type")
                if not request.year and media_info.get("year"):
                    request.year = media_info.get("year")
        
        # 执行搜索（支持多源索引器、去重、缓存、查询扩展）
        # Phase 9: 优先使用索引搜索，否则使用原有搜索
        results = []
        
        if indexed_service and search_query:
            # 使用索引优先搜索
            try:
                indexed_query = IndexedSearchQuery(
                    keyword=search_query,
                    category=request.media_type,
                    site_ids=request.sites,
                    hr_filter="exclude_hr" if request.exclude and "hr" in request.exclude.lower() else "any",
                    min_seeders=request.min_seeders,
                    max_seeders=request.max_seeders,
                    min_size_gb=request.min_size,
                    max_size_gb=request.max_size,
                    sort="seeders" if (request.sort_by or "seeders") == "seeders" else "published_at",
                    limit=request.page_size or 50,
                    offset=(request.page or 1 - 1) * (request.page_size or 50),
                )
                
                indexed_results = await indexed_service.search(indexed_query)
                
                # 转换为原有格式（保持向后兼容）
                for item in indexed_results:
                    results.append({
                        "title": item.title_raw,
                        "site": item.site_id,
                        "site_id": item.site_id,
                        "torrent_id": item.torrent_id,
                        "size_gb": item.size_gb or 0,
                        "seeders": item.seeders,
                        "leechers": item.leechers,
                        "upload_date": item.published_at,
                        "category": item.category,
                        "is_hr": item.is_hr,
                        "is_free": item.is_free,
                        "is_half_free": item.is_half_free,
                        "intel_hr_status": item.intel_hr_status,
                        "intel_site_status": item.intel_site_status,
                        "magnet_link": item.magnet_link,
                        "torrent_url": item.torrent_url,
                        "source": item.source,  # Phase EXT-4: 传递来源标记
                    })
                
                logger.info(f"IndexedSearchService: 返回 {len(results)} 条结果")
            except Exception as e:
                logger.warning(f"IndexedSearchService 搜索失败，回退到原有搜索: {e}")
                indexed_service = None  # 标记为失败，使用回退
        
        if not indexed_service or not results:
            # 使用基础search方法，它已经支持查询扩展、去重、缓存
            results = await service.search(
                query=search_query,
                media_type=request.media_type,
                year=request.year,
                quality=request.quality,
                resolution=request.resolution,
                min_size=request.min_size,
                max_size=request.max_size,
                min_seeders=request.min_seeders,
                max_seeders=request.max_seeders,
                include=request.include,
                exclude=request.exclude,
                sites=request.sites,
                sort_by=request.sort_by or "seeders",
                sort_order=request.sort_order or "desc",
                enable_query_expansion=True  # 启用查询扩展（针对老电视剧）
            )
        
        # 如果通过ID搜索，将媒体信息添加到结果中
        if media_info:
            for result in results:
                result["media_info"] = media_info
        
        # 智能分组
        grouped_results = None
        if request.group_by:
            grouped_results = service.group_results(results, request.group_by)
        
        # 分页处理
        total = len(results)
        page = request.page or 1
        page_size = request.page_size or 50
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]
        
        # 构建响应数据
        response_data = {
            "items": paginated_results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
        if grouped_results:
            response_data["grouped_results"] = grouped_results
        
        if media_info:
            response_data["media_info"] = media_info
        
        # 保存搜索历史（后台任务）
        filters_dict = {}
        if request.tmdb_id:
            filters_dict["tmdb_id"] = request.tmdb_id
        if request.imdb_id:
            filters_dict["imdb_id"] = request.imdb_id
        if request.douban_id:
            filters_dict["douban_id"] = request.douban_id
        if request.media_type:
            filters_dict["media_type"] = request.media_type
        if request.year:
            filters_dict["year"] = request.year
        if request.quality:
            filters_dict["quality"] = request.quality
        if request.resolution:
            filters_dict["resolution"] = request.resolution
        if request.language:
            filters_dict["language"] = request.language
        if request.category:
            filters_dict["category"] = request.category
        if request.encoding:
            filters_dict["encoding"] = request.encoding
        if request.source:
            filters_dict["source"] = request.source
        if request.min_size:
            filters_dict["min_size"] = request.min_size
        if request.max_size:
            filters_dict["max_size"] = request.max_size
        if request.min_seeders:
            filters_dict["min_seeders"] = request.min_seeders
        if request.max_seeders:
            filters_dict["max_seeders"] = request.max_seeders
        if request.include:
            filters_dict["include"] = request.include
        if request.exclude:
            filters_dict["exclude"] = request.exclude
        if request.sites:
            filters_dict["sites"] = request.sites
        
        background_tasks.add_task(
            service.save_search_history,
            search_query or f"ID:{request.tmdb_id or request.imdb_id or request.douban_id}",
            total,
            request.media_type,
            filters_dict if filters_dict else None,
            None  # user_id，可以从当前用户获取
        )
        
        return success_response(data=response_data, message="搜索成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行搜索时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/stream", response_class=StreamingResponse)
async def search_stream(
    request: SearchRequest,
    db = Depends(get_db)
):
    """
    使用SSE流式推送搜索结果
    
    返回SSE流，实时推送搜索结果
    """
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_search_stream():
        try:
            service = SearchService(db)
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始搜索...'})}\n\n"
            
            # 如果通过媒体ID搜索，先获取媒体信息
            media_info = None
            search_query = request.query
            
            if request.tmdb_id or request.imdb_id or request.douban_id:
                media_info = await service.get_media_info_by_id(
                    tmdb_id=request.tmdb_id,
                    imdb_id=request.imdb_id,
                    douban_id=request.douban_id,
                    media_type=request.media_type
                )
                if media_info:
                    yield f"data: {json.dumps({'type': 'media_info', 'data': media_info})}\n\n"
                    search_query = media_info.get("title") or search_query
            
            # 使用增强版搜索（支持多源索引器、去重、缓存、查询扩展）
            # 实时推送搜索进度
            total_results = []
            
            # 获取索引器列表（用于进度推送）
            indexer_manager = service.indexer_manager
            all_indexers = indexer_manager.get_all_indexers()
            enabled_indexers = [idx for idx in all_indexers if idx.is_healthy()]
            indexer_count = len(enabled_indexers) if enabled_indexers else 1
            
            # 发送索引器信息
            yield f"data: {json.dumps({'type': 'indexers', 'total': indexer_count, 'indexers': [idx.name for idx in enabled_indexers], 'message': f'开始搜索 {indexer_count} 个索引器...'})}\n\n"
            
            # 跟踪每个索引器的进度
            indexer_progress = {}
            completed_indexers = 0
            
            # 如果指定了站点，使用多源索引器搜索；否则使用基础搜索
            if request.sites:
                # 使用多源索引器搜索（带进度推送）
                selected_indexers = [
                    idx for idx in enabled_indexers
                    if idx.name.lower() in [s.lower() for s in request.sites]
                ]
                
                search_tasks = []
                for indexer in selected_indexers:
                    task = asyncio.create_task(
                        indexer_manager._search_with_timeout(
                            indexer,
                            search_query,
                            request.media_type,
                            request.year,
                            30,
                            quality=request.quality,
                            resolution=request.resolution,
                            min_size=request.min_size,
                            max_size=request.max_size,
                            min_seeders=request.min_seeders,
                            max_seeders=request.max_seeders,
                            include=request.include,
                            exclude=request.exclude,
                            language=request.language,
                            category=request.category,
                            encoding=request.encoding,
                            source=request.source
                        )
                    )
                    search_tasks.append((indexer, task))
                
                all_results = []
                for indexer, task in search_tasks:
                    try:
                        indexer_results = await task
                        if indexer_results:
                            all_results.extend(indexer_results)
                            completed_indexers += 1
                            indexer_progress[indexer.name] = {
                                'status': 'completed',
                                'count': len(indexer_results)
                            }
                            yield f"data: {json.dumps({'type': 'indexer_progress', 'indexer': indexer.name, 'status': 'completed', 'count': len(indexer_results), 'completed': completed_indexers, 'total': len(selected_indexers)})}\n\n"
                    except Exception as e:
                        logger.error(f"索引器 {indexer.name} 搜索异常: {e}")
                        completed_indexers += 1
                        indexer_progress[indexer.name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        yield f"data: {json.dumps({'type': 'indexer_progress', 'indexer': indexer.name, 'status': 'error', 'error': str(e), 'completed': completed_indexers, 'total': len(selected_indexers)})}\n\n"
                
                # 使用增强版聚合器（去重、评分、排序）
                yield f"data: {json.dumps({'type': 'aggregating', 'message': '正在聚合和去重搜索结果...'})}\n\n"
                results = service.aggregator.aggregate(
                    all_results,
                    sort_by=request.sort_by or "score",
                    sort_order=request.sort_order or "desc"
                )
            else:
                # 使用基础搜索（支持查询扩展、去重、缓存）
                yield f"data: {json.dumps({'type': 'searching', 'message': '正在搜索...'})}\n\n"
                results = await service.search(
                    query=search_query,
                    media_type=request.media_type,
                    year=request.year,
                    quality=request.quality,
                    resolution=request.resolution,
                    min_size=request.min_size,
                    max_size=request.max_size,
                    min_seeders=request.min_seeders,
                    max_seeders=request.max_seeders,
                    include=request.include,
                    exclude=request.exclude,
                    sites=request.sites,
                    sort_by=request.sort_by or "score",
                    sort_order=request.sort_order or "desc",
                    enable_query_expansion=True  # 启用查询扩展
                )
            
            # 分批发送结果（实时推送进度）
            batch_size = 10
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                total_results.extend(batch)
                progress = min(100, int((i + len(batch)) / len(results) * 100)) if results else 100
                yield f"data: {json.dumps({'type': 'results', 'data': batch, 'index': i, 'total': len(results), 'progress': progress})}\n\n"
                await asyncio.sleep(0.05)  # 减少延迟，提升响应速度
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'total': len(total_results), 'message': f'搜索完成，共找到 {len(total_results)} 条结果'})}\n\n"
            
        except Exception as e:
            logger.error(f"SSE搜索流错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_search_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/history", response_model=BaseResponse)
async def get_search_history(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    query: Optional[str] = Query(None, description="搜索关键词过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    db = Depends(get_db)
):
    """
    获取搜索历史
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [SearchHistory, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        history = await service.get_search_history(limit=limit, query=query, user_id=user_id)
        return success_response(data=history, message="获取成功")
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取搜索历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/history/{history_id}", response_model=BaseResponse)
async def delete_search_history(
    history_id: int,
    db = Depends(get_db)
):
    """
    删除搜索历史
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        success = await service.delete_search_history(history_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"搜索历史不存在 (ID: {history_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除搜索历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/history", response_model=BaseResponse)
async def clear_search_history(
    user_id: Optional[int] = Query(None, description="用户ID，如果为空则清空所有"),
    db = Depends(get_db)
):
    """
    清空搜索历史
    
    返回统一响应格式：
    {
        "success": true,
        "message": "清空成功",
        "data": {
            "deleted_count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        count = await service.clear_search_history(user_id=user_id)
        return success_response(
            data={"deleted_count": count},
            message=f"清空成功，已删除 {count} 条记录"
        )
    except Exception as e:
        logger.error(f"清空搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清空搜索历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/indexers/status", response_model=BaseResponse)
async def get_indexer_statuses(
    db = Depends(get_db)
):
    """
    获取所有索引器的状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "indexer_name": {
                "name": "...",
                "base_url": "...",
                "enabled": true,
                "healthy": true,
                "error_count": 0,
                ...
            },
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        statuses = await service.get_indexer_statuses()
        return success_response(data=statuses, message="获取成功")
    except Exception as e:
        logger.error(f"获取索引器状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取索引器状态时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/indexers/health-check", response_model=BaseResponse)
async def health_check_indexers(
    db = Depends(get_db)
):
    """
    检查所有索引器的健康状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "健康检查完成",
        "data": {
            "indexer_name": true/false,
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        health_results = await service.health_check_all_indexers()
        return success_response(data=health_results, message="健康检查完成")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"健康检查时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/suggestions", response_model=BaseResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取搜索建议
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "suggestions": ["suggestion1", "suggestion2", ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SearchService(db)
        suggestions = await service.get_suggestions(query, limit=limit)
        return success_response(
            data={"suggestions": suggestions},
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取搜索建议时发生错误: {str(e)}"
            ).model_dump()
        )

