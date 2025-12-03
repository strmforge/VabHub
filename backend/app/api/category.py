"""
分类配置API
用于管理媒体分类的YAML配置文件
"""

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.media_types import is_tv_like
from app.core.database import get_db
from app.core.schemas import BaseResponse, error_response, success_response

router = APIRouter(prefix="/category", tags=["分类配置"])


class CategoryConfigResponse(BaseModel):
    """分类配置响应"""
    content: str
    path: str


class CategoryConfigUpdateRequest(BaseModel):
    """更新分类配置请求"""
    content: str


class CategoryPreviewRequest(BaseModel):
    """分类预览请求"""
    media_type: str  # movie, tv, music
    tmdb_data: Dict[str, Any]


class CategoryPreviewResponse(BaseModel):
    """分类预览响应"""
    category: str
    matched_rules: Dict[str, Any]


def get_category_config_path() -> Path:
    """获取分类配置文件路径"""
    base_dir = Path(__file__).parent.parent.parent.parent
    config_path = base_dir / "config" / "category.yaml"
    return config_path


@router.get("/config", response_model=BaseResponse)
async def get_category_config():
    """
    获取分类配置文件内容
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "content": "...",
            "path": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        config_path = get_category_config_path()
        
        if not config_path.exists():
            # 如果配置文件不存在，返回默认配置
            from app.modules.media_renamer.category_helper import CategoryHelper
            helper = CategoryHelper(config_path)
            # 重新初始化以创建默认配置
            helper.init()
        
        # 读取配置文件内容
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return success_response(
            data={
                "content": content,
                "path": str(config_path)
            },
            message="获取分类配置成功"
        )
    except Exception as e:
        logger.error(f"获取分类配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取分类配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/config", response_model=BaseResponse)
async def update_category_config(request: CategoryConfigUpdateRequest):
    """
    更新分类配置文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": {
            "path": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        config_path = get_category_config_path()
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 验证YAML格式
        try:
            import ruamel.yaml
            yaml = ruamel.yaml.YAML()
            yaml.load(request.content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_YAML_FORMAT",
                    error_message=f"YAML格式错误: {str(e)}"
                ).model_dump()
            )
        
        # 保存配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        # 重新加载分类助手
        from app.modules.media_renamer.category_helper import CategoryHelper
        helper = CategoryHelper(config_path)
        helper.reload()
        
        logger.info(f"分类配置已更新: {config_path}")
        
        return success_response(
            data={"path": str(config_path)},
            message="更新分类配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分类配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新分类配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/preview", response_model=BaseResponse)
async def preview_category(request: CategoryPreviewRequest):
    """
    预览分类结果
    
    返回统一响应格式：
    {
        "success": true,
        "message": "预览成功",
        "data": {
            "category": "...",
            "matched_rules": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.media_renamer.category_helper import CategoryHelper
        
        config_path = get_category_config_path()
        helper = CategoryHelper(config_path)
        
        category = ""
        matched_rules = {}
        
        if request.media_type == "movie":
            category = helper.get_movie_category(request.tmdb_data)
        elif is_tv_like(request.media_type):
            category = helper.get_tv_category(request.tmdb_data)
        elif request.media_type == "music":
            category = helper.get_music_category(request.tmdb_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_MEDIA_TYPE",
                    error_message=f"不支持的媒体类型: {request.media_type}"
                ).model_dump()
            )
        
        # 提取匹配的规则信息
        if category:
            if request.media_type == "movie":
                categories = helper._movie_categorys
            elif is_tv_like(request.media_type):
                categories = helper._tv_categorys
            else:
                categories = helper._music_categorys
            
            if category in categories:
                matched_rules = categories[category] or {}
        
        return success_response(
            data={
                "category": category or "未分类",
                "matched_rules": matched_rules
            },
            message="预览分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"预览分类时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/list", response_model=BaseResponse)
async def list_categories():
    """
    获取所有分类列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "movie": [...],
            "tv": [...],
            "music": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.media_renamer.category_helper import CategoryHelper
        
        config_path = get_category_config_path()
        helper = CategoryHelper(config_path)
        
        return success_response(
            data={
                "movie": helper.movie_categorys,
                "tv": helper.tv_categorys,
                "music": helper.music_categorys
            },
            message="获取分类列表成功"
        )
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取分类列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/reload", response_model=BaseResponse)
async def reload_category_config():
    """
    重新加载分类配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "重新加载成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.media_renamer.category_helper import CategoryHelper
        
        config_path = get_category_config_path()
        helper = CategoryHelper(config_path)
        helper.reload()
        
        logger.info("分类配置已重新加载")
        
        return success_response(
            data=None,
            message="重新加载分类配置成功"
        )
    except Exception as e:
        logger.error(f"重新加载分类配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重新加载分类配置时发生错误: {str(e)}"
            ).model_dump()
        )

