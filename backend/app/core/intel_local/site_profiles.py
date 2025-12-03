"""
站点配置文件加载器
扫描并解析 config/intel_sites/*.yaml 配置文件
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List, TYPE_CHECKING
import yaml
from loguru import logger

from app.core.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.site import Site


@dataclass
class HRConfig:
    """HR 配置"""
    enabled: bool = False
    mode: Optional[str] = None  # "TASK_LIST" 等
    disappear_semantics: str = "UNKNOWN"  # "FINISHED" 或 "UNKNOWN"
    max_observe_days: int = 60
    hr_page_url: Optional[str] = None
    page_path: Optional[str] = None  # HR 页面路径（如 "hr.php"），优先使用此字段


@dataclass
class InboxConfig:
    """站内信配置"""
    enabled: bool = False
    parser: Optional[str] = None  # "nexusphp_inbox", "ttg_inbox" 等
    pm_keywords: Dict[str, List[str]] = field(default_factory=dict)  # penalty, delete, throttle
    page_path: Optional[str] = None  # 站内信页面路径（如 "messages.php"）


@dataclass
class SiteGuardConfig:
    """站点防护配置"""
    enabled: bool = True
    default_safe_scan_minutes: int = 10
    default_safe_pages_per_hour: int = 200


@dataclass
class IntelSiteProfile:
    """站点智能配置"""
    site: str
    hr: HRConfig = field(default_factory=HRConfig)
    inbox: InboxConfig = field(default_factory=InboxConfig)
    site_guard: SiteGuardConfig = field(default_factory=SiteGuardConfig)

    @classmethod
    def from_dict(cls, data: dict) -> IntelSiteProfile:
        """从字典创建配置对象"""
        site = data.get("site", "")
        if not site:
            raise ValueError("站点配置缺少 'site' 字段")

        # 解析 HR 配置
        hr_data = data.get("hr", {})
        hr_config = HRConfig(
            enabled=hr_data.get("enabled", False),
            mode=hr_data.get("mode"),
            disappear_semantics=hr_data.get("disappear_semantics", "UNKNOWN"),
            max_observe_days=hr_data.get("max_observe_days", 60),
            hr_page_url=hr_data.get("hr_page_url"),
            page_path=hr_data.get("page_path") or hr_data.get("hr_page_path") or "hr.php",
        )

        # 解析 Inbox 配置
        inbox_data = data.get("inbox", {})
        inbox_config = InboxConfig(
            enabled=inbox_data.get("enabled", False),
            parser=inbox_data.get("parser"),
            pm_keywords=inbox_data.get("pm_keywords", {}),
            page_path=inbox_data.get("page_path") or inbox_data.get("inbox_page_path") or "messages.php",
        )

        # 解析 Site Guard 配置
        guard_data = data.get("site_guard", {})
        site_guard_config = SiteGuardConfig(
            enabled=guard_data.get("enabled", True),
            default_safe_scan_minutes=guard_data.get("default_safe_scan_minutes", 10),
            default_safe_pages_per_hour=guard_data.get("default_safe_pages_per_hour", 200),
        )

        return cls(
            site=site,
            hr=hr_config,
            inbox=inbox_config,
            site_guard=site_guard_config,
        )


class SiteProfileLoader:
    """站点配置加载器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录路径（默认: config/intel_sites）
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认路径：项目根目录下的 config/intel_sites
            # 从 backend/app/core/intel_local/site_profiles.py 向上找到项目根目录
            # backend/app/core/intel_local/site_profiles.py -> backend/app/core/intel_local -> backend/app/core -> backend/app -> backend -> 项目根目录
            backend_dir = Path(__file__).parent.parent.parent.parent  # backend 目录
            project_root = backend_dir.parent  # 项目根目录（VabHub）
            self.config_dir = project_root / "config" / "intel_sites"
        
        self.profiles: Dict[str, IntelSiteProfile] = {}

    def load_all(self) -> Dict[str, IntelSiteProfile]:
        """
        加载所有站点配置文件
        
        Returns:
            站点配置字典，key 为站点名，value 为 IntelSiteProfile
        """
        if not self.config_dir.exists():
            logger.warning(f"LocalIntel 配置目录不存在: {self.config_dir}，跳过加载")
            return {}

        profiles = {}
        yaml_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        
        if not yaml_files:
            logger.warning(f"LocalIntel 配置目录中没有找到 YAML 文件: {self.config_dir}")
            return {}

        for yaml_file in yaml_files:
            try:
                profile = self._load_site_profile(yaml_file)
                if profile:
                    profiles[profile.site] = profile
                    logger.info(f"已加载站点配置: {profile.site} ({yaml_file.name})")
            except Exception as e:
                logger.error(f"加载站点配置文件失败 {yaml_file}: {e}", exc_info=True)

        self.profiles = profiles
        logger.info(f"LocalIntel 站点配置加载完成: {len(profiles)} 个站点")
        return profiles

    def _load_site_profile(self, yaml_file: Path) -> Optional[IntelSiteProfile]:
        """加载单个站点配置文件"""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, dict):
                logger.warning(f"配置文件格式无效: {yaml_file}")
                return None

            return IntelSiteProfile.from_dict(data)
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析失败 {yaml_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载站点配置失败 {yaml_file}: {e}")
            return None

    def get_profile(self, site: str) -> Optional[IntelSiteProfile]:
        """获取指定站点的配置"""
        return self.profiles.get(site)

    def get_all_profiles(self) -> Dict[str, IntelSiteProfile]:
        """获取所有站点配置"""
        return self.profiles.copy()


# 全局单例
_site_profile_loader: Optional[SiteProfileLoader] = None


def get_site_profile_loader() -> SiteProfileLoader:
    """获取站点配置加载器单例"""
    global _site_profile_loader
    if _site_profile_loader is None:
        _site_profile_loader = SiteProfileLoader()
    return _site_profile_loader


def get_site_profile(site: str) -> Optional[IntelSiteProfile]:
    """获取指定站点的配置"""
    loader = get_site_profile_loader()
    # 如果配置未加载，自动加载
    if not loader.profiles:
        loader.load_all()
    return loader.get_profile(site)


async def get_site_profile_with_ai_fallback(
    site: str,
    site_obj: Optional["Site"] = None,
    db: Optional["AsyncSession"] = None,
) -> Optional[IntelSiteProfile]:
    """
    获取站点配置，支持 AI 配置回退
    
    Phase AI-2: 优先使用手工配置，如果没有则尝试从 AI 配置转换
    
    Args:
        site: 站点标识（字符串）
        site_obj: 站点对象（可选，如果提供则用于 AI 配置转换）
        db: 数据库会话（可选，如果提供则用于加载 AI 配置）
        
    Returns:
        IntelSiteProfile 或 None
    """
    # 1. 优先使用手工配置
    profile = get_site_profile(site)
    if profile:
        logger.debug(f"站点 {site} 使用手工配置")
        return profile
    
    # 2. 如果没有手工配置，尝试从 AI 配置转换
    if not settings.AI_ADAPTER_ENABLED:
        logger.debug(f"AI 适配功能已禁用，跳过 AI 配置回退 (site: {site})")
        return None
    
    if not site_obj or not db:
        logger.debug(f"缺少站点对象或数据库会话，无法使用 AI 配置回退 (site: {site})")
        return None
    
    try:
        from app.core.site_ai_adapter import load_parsed_config
        from app.core.site_ai_adapter.intel_bridge import ai_config_to_intel_profile
        from app.models.ai_site_adapter import AISiteAdapter
        from sqlalchemy import select as sql_select
        
        # Phase AI-4: 检查站点级别的禁用标志和优先策略
        ai_record_result = await db.execute(
            sql_select(AISiteAdapter).where(AISiteAdapter.site_id == str(site_obj.id))
        )
        ai_record = ai_record_result.scalar_one_or_none()
        
        if ai_record:
            # 检查是否禁用
            if ai_record.disabled:
                logger.debug(f"站点 {site} 的 AI 适配已禁用（站点级别），跳过 AI 配置回退")
                return None
            
            # 检查是否优先人工配置（如果存在手工配置，应该已经在步骤 1 返回了）
            # 这里主要是防御性检查
            if ai_record.manual_profile_preferred:
                # 再次检查是否有手工配置（可能是在步骤 1 之后才加载的）
                manual_profile_retry = get_site_profile(site)
                if manual_profile_retry:
                    logger.debug(f"站点 {site} 设置了优先人工配置，且存在手工配置，使用手工配置")
                    return manual_profile_retry
        
        # 加载 AI 配置
        ai_cfg = await load_parsed_config(str(site_obj.id), db)
        if not ai_cfg:
            logger.debug(f"站点 {site} 没有 AI 适配配置")
            return None
        
        # 转换为 Intel Profile
        profile = ai_config_to_intel_profile(site_obj, ai_cfg)
        if profile:
            logger.info(f"站点 {site} 使用 AI 生成的配置（回退模式）")
        
        return profile
        
    except Exception as e:
        logger.warning(
            f"从 AI 配置回退获取站点配置失败 (site: {site}): {e}",
            exc_info=True
        )
        return None


def get_all_site_profiles() -> Dict[str, IntelSiteProfile]:
    """获取所有站点配置"""
    loader = get_site_profile_loader()
    # 如果配置未加载，自动加载
    if not loader.profiles:
        loader.load_all()
    return loader.get_all_profiles()


def load_all_site_profiles(config_dir: Optional[str] = None) -> Dict[str, IntelSiteProfile]:
    """
    显式加载 config/intel_sites 目录（Phase 2 指南要求）
    """
    loader = get_site_profile_loader()
    if config_dir:
        loader.config_dir = Path(config_dir)
    return loader.load_all()

