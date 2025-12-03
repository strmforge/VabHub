"""
站点 AI 适配服务

封装「抓 HTML → 调 CF → 存库」整体流程。
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

import httpx
from app.models.site import Site
from app.core.site_ai_adapter.client import call_cf_adapter, AIAdapterClientError
from app.core.site_ai_adapter.models import (
    SiteAIAdapterResult,
    AISiteAdapterConfig,
    ParsedAISiteAdapterConfig,
)
from app.core.config import settings


async def analyze_and_save_for_site(
    site_id: str,
    db: AsyncSession,
) -> Optional[SiteAIAdapterResult]:
    """
    分析站点并保存适配配置
    
    流程：
    1. 从数据库加载站点信息 Site（含 base_url 和 engine 类型）
    2. 用现有的 HTTP 客户端抓取三个页面 HTML：
       - 登录页
       - 列表页
       - 详情页（可选：找一个有内容的种子）
    3. 调用 client.call_cf_adapter(...)
    4. 把结果写入数据库（新建/更新一条记录）
    5. 返回结果
    
    Args:
        site_id: 站点 ID
        db: 数据库会话
        
    Returns:
        SiteAIAdapterResult 或 None（如果失败）
    """
    if not settings.AI_ADAPTER_ENABLED:
        logger.warning("AI 适配功能已禁用")
        return None
    
    try:
        # 1. 从数据库加载站点信息
        result = await db.execute(select(Site).where(Site.id == int(site_id)))
        site = result.scalar_one_or_none()
        
        if not site:
            logger.error(f"站点不存在: {site_id}")
            return None
        
        site_url = site.url.rstrip("/")
        site_name = site.name
        cookies = site.cookie or ""
        
        # 推断站点框架类型（TODO: 可以从站点配置或数据库字段读取）
        # 目前先默认使用 nexusphp，后续可以从站点配置中读取
        engine = "nexusphp"  # TODO: 从站点配置或数据库字段读取实际框架类型
        
        logger.info(f"开始分析站点: {site_name} ({site_id})")
        
        # 2. 创建 HTTP 客户端并抓取 HTML
        # 解析 Cookie
        cookie_dict = {}
        if cookies:
            for item in cookies.split(";"):
                item = item.strip()
                if "=" in item:
                    key, value = item.split("=", 1)
                    cookie_dict[key.strip()] = value.strip()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=headers,
            cookies=cookie_dict,
        ) as http_client:
            # 抓取登录页 HTML
            login_html = ""
            try:
                # 尝试访问登录页（常见路径）
                login_paths = ["login.php", "user.php?action=login", "index.php?action=login"]
                for path in login_paths:
                    try:
                        url = f"{site_url}/{path.lstrip('/')}"
                        response = await http_client.get(url)
                        response.raise_for_status()
                        login_html = response.text
                        logger.debug(f"成功获取登录页 HTML (路径: {path})")
                        break
                    except Exception as e:
                        logger.debug(f"尝试路径 {path} 失败: {e}")
                        continue
            except Exception as e:
                logger.warning(f"获取登录页 HTML 失败: {e}，继续使用空内容")
            
            # 抓取种子列表页 HTML
            torrents_html = ""
            try:
                # 尝试访问种子列表页（常见路径）
                list_paths = ["torrents.php", "browse.php", "index.php"]
                for path in list_paths:
                    try:
                        url = f"{site_url}/{path.lstrip('/')}"
                        response = await http_client.get(url)
                        response.raise_for_status()
                        torrents_html = response.text
                        logger.debug(f"成功获取种子列表页 HTML (路径: {path})")
                        break
                    except Exception as e:
                        logger.debug(f"尝试路径 {path} 失败: {e}")
                        continue
                
                if not torrents_html:
                    raise Exception("无法获取种子列表页 HTML")
            except Exception as e:
                logger.error(f"获取种子列表页 HTML 失败: {e}")
                raise
            
            # 抓取种子详情页 HTML（可选）
            detail_html = ""
            try:
                # 尝试从列表页中提取一个种子 ID，然后访问详情页
                # 这里简化处理：尝试访问一个示例详情页
                # TODO: 可以从列表页 HTML 中解析出真实的种子 ID
                detail_paths = ["details.php?id=1", "torrents.php?id=1", "view.php?id=1"]
                for path in detail_paths:
                    try:
                        url = f"{site_url}/{path.lstrip('/')}"
                        response = await http_client.get(url)
                        response.raise_for_status()
                        detail_html = response.text
                        logger.debug(f"成功获取种子详情页 HTML (路径: {path})")
                        break
                    except Exception as e:
                        logger.debug(f"尝试路径 {path} 失败: {e}")
                        continue
            except Exception as e:
                logger.warning(f"获取种子详情页 HTML 失败: {e}，继续使用空内容")
            
            # 3. 调用 Cloudflare API
            result = await call_cf_adapter(
                site_id=site_id,
                site_name=site_name,
                site_url=site_url,
                engine=engine,
                login_html=login_html,
                torrents_html=torrents_html,
                detail_html=detail_html,
            )
            
            if not result:
                logger.error(f"AI 适配分析失败: 返回 None")
                return None
            
            # 4. 保存到数据库
            from app.models.ai_site_adapter import AISiteAdapter
            from datetime import datetime
            
            # 检查是否已存在记录
            existing = await db.execute(
                select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
            )
            existing_record = existing.scalar_one_or_none()
            
            if existing_record:
                # 更新现有记录
                existing_record.engine = result.engine
                existing_record.config_json = result.config.model_dump()
                existing_record.raw_model_output = result.raw_model_output
                existing_record.confidence_score = 80  # Phase AI-4: 固定可信度分数
                existing_record.last_error = None  # Phase AI-4: 清空错误
                existing_record.updated_at = datetime.utcnow()
                logger.info(f"更新站点适配配置: {site_id}")
            else:
                # 创建新记录
                new_record = AISiteAdapter(
                    site_id=site_id,
                    engine=result.engine,
                    config_json=result.config.model_dump(),
                    raw_model_output=result.raw_model_output,
                    version=1,
                    confidence_score=80,  # Phase AI-4: 固定可信度分数
                    last_error=None,  # Phase AI-4: 清空错误
                )
                db.add(new_record)
                logger.info(f"创建站点适配配置: {site_id}")
            
            await db.commit()
            
            logger.info(f"站点适配分析完成: {site_name} ({site_id})")
            return result
            
    except AIAdapterClientError as e:
        logger.error(f"AI 适配客户端错误: {e}")
        # Phase AI-4: 调用失败时，更新/创建记录并保存错误信息
        try:
            from app.models.ai_site_adapter import AISiteAdapter
            from datetime import datetime
            
            existing = await db.execute(
                select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
            )
            existing_record = existing.scalar_one_or_none()
            
            error_message = str(e)[:500]  # 限制错误信息长度
            
            if existing_record:
                # 更新现有记录的错误信息，保留旧配置
                existing_record.last_error = error_message
                existing_record.updated_at = datetime.utcnow()
            else:
                # 创建新记录，只保存错误信息（没有配置）
                # 注意：这种情况下 config_json 需要有一个占位值
                new_record = AISiteAdapter(
                    site_id=site_id,
                    engine="unknown",
                    config_json={},  # 空配置占位
                    raw_model_output=None,
                    version=1,
                    disabled=False,
                    manual_profile_preferred=False,
                    confidence_score=None,
                    last_error=error_message,
                )
                db.add(new_record)
            
            await db.commit()
            logger.info(f"已保存 AI 适配错误信息到数据库 (site_id: {site_id})")
        except Exception as save_error:
            logger.warning(f"保存错误信息到数据库失败: {save_error}")
            await db.rollback()
        
        return None
    except Exception as e:
        logger.error(f"分析站点时发生错误: {e}", exc_info=True)
        # Phase AI-4: 其他异常也尝试保存错误信息
        try:
            from app.models.ai_site_adapter import AISiteAdapter
            from datetime import datetime
            
            existing = await db.execute(
                select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
            )
            existing_record = existing.scalar_one_or_none()
            
            error_message = str(e)[:500]
            
            if existing_record:
                existing_record.last_error = error_message
                existing_record.updated_at = datetime.utcnow()
            else:
                new_record = AISiteAdapter(
                    site_id=site_id,
                    engine="unknown",
                    config_json={},
                    raw_model_output=None,
                    version=1,
                    disabled=False,
                    manual_profile_preferred=False,
                    confidence_score=None,
                    last_error=error_message,
                )
                db.add(new_record)
            
            await db.commit()
        except Exception:
            pass  # 忽略保存错误信息时的异常
        
        await db.rollback()
        return None


async def get_site_adapter_config(
    site_id: str,
    db: AsyncSession,
) -> Optional[dict]:
    """
    获取站点的适配配置（从数据库读取）
    
    Args:
        site_id: 站点 ID
        db: 数据库会话
        
    Returns:
        配置字典或 None
    """
    try:
        from app.models.ai_site_adapter import AISiteAdapter
        
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return None
        
        return record.config_json
        
    except Exception as e:
        logger.error(f"获取站点适配配置失败: {e}")
        return None


async def load_parsed_config(
    site_id: str,
    db: AsyncSession,
) -> Optional[ParsedAISiteAdapterConfig]:
    """
    从数据库加载并解析站点 AI 适配配置
    
    Phase AI-2: 类型安全的配置视图层
    
    Args:
        site_id: 站点 ID（字符串格式）
        db: 数据库会话
        
    Returns:
        ParsedAISiteAdapterConfig 或 None（如果不存在或解析失败）
    """
    try:
        from app.models.ai_site_adapter import AISiteAdapter
        
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            logger.debug(f"站点 {site_id} 没有 AI 适配配置记录")
            return None
        
        # 解析 JSON 配置
        config_dict = record.config_json
        if not config_dict or not isinstance(config_dict, dict):
            logger.warning(f"站点 {site_id} 的 AI 配置 JSON 格式无效")
            return None
        
        try:
            # 使用 Pydantic 验证配置结构
            ai_config = AISiteAdapterConfig(**config_dict)
            
            # 转换为解析后的配置
            parsed_config = ParsedAISiteAdapterConfig.from_ai_config(
                site_id=site_id,
                engine=record.engine,
                config=ai_config,
            )
            
            # Phase AI-4: 从数据库记录中读取 confidence_score
            parsed_config.confidence_score = record.confidence_score
            
            logger.debug(f"成功加载并解析站点 {site_id} 的 AI 适配配置")
            return parsed_config
            
        except Exception as e:
            logger.warning(
                f"解析站点 {site_id} 的 AI 适配配置失败: {e}",
                exc_info=True
            )
            return None
            
    except Exception as e:
        logger.error(f"加载站点 {site_id} 的 AI 适配配置时发生错误: {e}", exc_info=True)
        return None


async def maybe_auto_analyze_site(site_id: str, db: AsyncSession) -> Optional[SiteAIAdapterResult]:
    """
    如果 AI 适配功能开启，则为指定站点触发一次分析并保存结果。
    
    Phase AI-3: 增加频率限制，避免短时间内重复分析
    
    失败时只记录日志，不抛出异常。此函数设计为在后台任务中调用，不应阻塞主流程。
    
    注意：站点创建/更新完成后，可在适当位置调用此函数，实现自动适配。
    
    Args:
        site_id: 站点 ID（字符串格式，如 "1"）
        db: 数据库会话
        
    Returns:
        SiteAIAdapterResult 或 None（如果失败或未启用）
    """
    if not settings.AI_ADAPTER_ENABLED:
        logger.debug(f"AI 适配功能已禁用，跳过自动分析 (site_id: {site_id})")
        return None
    
    # Phase AI-4: 检查站点级别的禁用标志
    try:
        from app.models.ai_site_adapter import AISiteAdapter
        
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        existing_record = result.scalar_one_or_none()
        
        if existing_record and existing_record.disabled:
            logger.info(f"站点 {site_id} 的 AI 适配已禁用（站点级别），跳过自动分析")
            return None
    except Exception as e:
        logger.debug(f"检查站点 {site_id} 的禁用状态失败: {e}，继续执行分析")
    
    # Phase AI-3: 频率限制检查
    try:
        from app.models.ai_site_adapter import AISiteAdapter
        from datetime import datetime, timedelta
        
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        existing_record = result.scalar_one_or_none()
        
        if existing_record:
            # 检查上次分析时间
            last_analyzed = existing_record.updated_at or existing_record.created_at
            if last_analyzed:
                min_interval = timedelta(minutes=settings.AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES)
                time_since_last = datetime.utcnow() - last_analyzed.replace(tzinfo=None)
                
                if time_since_last < min_interval:
                    remaining_minutes = (min_interval - time_since_last).total_seconds() / 60
                    logger.info(
                        f"站点 {site_id} 在 {settings.AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES} 分钟内已分析过，"
                        f"跳过本次自动触发（还需等待 {remaining_minutes:.1f} 分钟）"
                    )
                    return None
    except Exception as e:
        logger.debug(f"检查站点 {site_id} 的分析频率限制失败: {e}，继续执行分析")
    
    try:
        logger.info(f"开始自动分析站点适配配置 (site_id: {site_id})")
        result = await analyze_and_save_for_site(site_id=site_id, db=db)
        
        if result:
            logger.info(f"站点适配配置分析成功 (site_id: {site_id})")
        else:
            logger.warning(f"站点适配配置分析返回 None (site_id: {site_id})")
        
        return result
        
    except Exception as e:
        # 所有异常都只记录日志，不向上抛出
        logger.warning(
            f"自动分析站点适配配置失败 (site_id: {site_id}): {e}",
            exc_info=True
        )
        return None

