"""
外部站点配置加载器

从 YAML 配置文件加载外部站点配置。
"""

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
import yaml
from loguru import logger

from app.core.ext_indexer.models import ExternalSiteConfig

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.site import Site

# 配置目录路径
_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config" / "external_sites"

# 缓存已加载的配置
_config_cache: Optional[List[ExternalSiteConfig]] = None


def load_all_site_configs() -> List[ExternalSiteConfig]:
    """
    加载所有外部站点配置
    
    遍历 config/external_sites/ 目录，解析所有 YAML 文件。
    单个文件失败只记录日志并忽略。
    
    Returns:
        站点配置列表
    """
    global _config_cache
    
    # 如果已缓存，直接返回
    if _config_cache is not None:
        return _config_cache
    
    configs: List[ExternalSiteConfig] = []
    
    # 检查配置目录是否存在
    if not _CONFIG_DIR.exists():
        logger.debug(f"外部站点配置目录不存在: {_CONFIG_DIR}")
        _config_cache = []
        return configs
    
    # 遍历所有 YAML 文件
    yaml_files = list(_CONFIG_DIR.glob("*.yaml")) + list(_CONFIG_DIR.glob("*.yml"))
    
    if not yaml_files:
        logger.debug(f"外部站点配置目录中没有 YAML 文件: {_CONFIG_DIR}")
        _config_cache = []
        return configs
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                logger.warning(f"配置文件 {yaml_file} 格式错误：不是字典格式")
                continue
            
            # 解析为 ExternalSiteConfig
            config = ExternalSiteConfig(**data)
            configs.append(config)
            logger.debug(f"已加载站点配置: {config.site_id} ({config.name})")
        except yaml.YAMLError as e:
            logger.warning(f"解析配置文件 {yaml_file} 失败: {e}")
            continue
        except Exception as e:
            logger.warning(f"加载配置文件 {yaml_file} 失败: {e}")
            continue
    
    logger.info(f"已加载 {len(configs)} 个外部站点配置")
    _config_cache = configs
    return configs


def get_site_config(site_id: str) -> Optional[ExternalSiteConfig]:
    """
    获取指定站点的配置（优先使用手工配置）
    
    Args:
        site_id: 站点 ID
        
    Returns:
        站点配置，如果不存在则返回 None
    """
    configs = load_all_site_configs()
    for config in configs:
        if config.site_id == site_id:
            return config
    return None


async def get_site_config_with_ai_fallback(
    site_id: str,
    site_obj: Optional["Site"] = None,
    db: Optional["AsyncSession"] = None,
) -> Optional[ExternalSiteConfig]:
    """
    获取站点配置，支持 AI 配置回退
    
    Phase AI-2: 优先使用手工配置，如果没有则尝试从 AI 配置转换
    
    Args:
        site_id: 站点 ID（字符串）
        site_obj: 站点对象（可选，如果提供则用于 AI 配置转换）
        db: 数据库会话（可选，如果提供则用于加载 AI 配置）
        
    Returns:
        ExternalSiteConfig 或 None
    """
    # 1. 优先使用手工配置
    config = get_site_config(site_id)
    if config:
        logger.debug(f"站点 {site_id} 使用手工配置")
        return config
    
    # 2. 如果没有手工配置，尝试从 AI 配置转换
    from app.core.config import settings
    if not settings.AI_ADAPTER_ENABLED:
        logger.debug(f"AI 适配功能已禁用，跳过 AI 配置回退 (site_id: {site_id})")
        return None
    
    if not site_obj or not db:
        logger.debug(f"缺少站点对象或数据库会话，无法使用 AI 配置回退 (site_id: {site_id})")
        return None
    
    try:
        from app.core.site_ai_adapter import load_parsed_config
        from app.core.ext_indexer.ai_bridge import ai_config_to_external_site_config
        from app.models.ai_site_adapter import AISiteAdapter
        from sqlalchemy import select as sql_select
        
        # Phase AI-4: 检查站点级别的禁用标志和优先策略
        ai_record_result = await db.execute(
            sql_select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        ai_record = ai_record_result.scalar_one_or_none()
        
        if ai_record:
            # 检查是否禁用
            if ai_record.disabled:
                logger.debug(f"站点 {site_id} 的 AI 适配已禁用（站点级别），跳过 AI 配置回退")
                return None
            
            # 检查是否优先人工配置
            if ai_record.manual_profile_preferred:
                # 再次检查是否有手工配置
                manual_config_retry = get_site_config(site_id)
                if manual_config_retry:
                    logger.debug(f"站点 {site_id} 设置了优先人工配置，且存在手工配置，使用手工配置")
                    return manual_config_retry
        
        # 加载 AI 配置
        ai_cfg = await load_parsed_config(str(site_obj.id), db)
        if not ai_cfg:
            logger.debug(f"站点 {site_id} 没有 AI 适配配置")
            return None
        
        # 转换为 External Site Config
        config = ai_config_to_external_site_config(site_obj, ai_cfg)
        if config:
            logger.info(f"站点 {site_id} 使用 AI 生成的配置（回退模式）")
        
        return config
        
    except Exception as e:
        logger.warning(
            f"从 AI 配置回退获取站点配置失败 (site_id: {site_id}): {e}",
            exc_info=True
        )
        return None


def clear_cache() -> None:
    """
    清除配置缓存（用于测试或热重载）
    """
    global _config_cache
    _config_cache = None
    logger.debug("外部站点配置缓存已清除")

