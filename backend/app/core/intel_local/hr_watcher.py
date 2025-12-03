"""
HR 页面监控器 (Phase 2)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, Mapping, Optional, Tuple, Any

from loguru import logger

from app.core.config import settings
from .hr_state import iter_site_states, update_from_hr_page, mark_from_hr_page_disappear
from .models import HRTorrentState
from .site_profiles import (
    IntelSiteProfile,
    get_all_site_profiles,
    get_site_profile,
)
from .http_clients import get_http_client_registry
from .parsers.hr_html_parser import (
    ParsedHRRow,
    parse_hr_page_generic,
    parse_hr_page_hdsky,
)
from .repo import HRCasesRepository

HR_PARSERS = {
    "hdsky": parse_hr_page_hdsky,
}

@dataclass
class HRRow:
    """单条 HR 任务行，来源于站点 HR 列表页面。"""

    torrent_id: str
    required_seed_hours: float
    seeded_hours: float
    deadline: Optional[datetime] = None


class HRWatcher:
    """从各站点 HR 页面刷新本地 HRTorrentState。

    设计思路：
    - handle_site() 是对外主要入口，由 scheduler 周期性调用。
    - fetch_hr_rows() 是 *留给主项目实现* 的抽象方法：
      - 如何带 Cookie、如何绕 Cloudflare、如何解析 HTML，都由项目自己的 HTTP 层完成。
    - 本类专注于“数据对比 + 状态机更新”，不关心 HTTP / HTML 细节。
    """

    def __init__(
        self,
        site_profiles: Optional[Mapping[str, IntelSiteProfile]] = None,
        hr_repo: HRCasesRepository | None = None,
    ) -> None:
        self._profiles: Dict[str, IntelSiteProfile] = dict(site_profiles or get_all_site_profiles())
        self._hr_repo = hr_repo

    def refresh_profiles(self) -> None:
        """外部可调用以刷新站点配置映射。"""
        self._profiles = dict(get_all_site_profiles())

    async def handle_site(self, site: str, profile: Optional[IntelSiteProfile] = None) -> Dict[str, Any]:
        profile = profile or self._profiles.get(site) or get_site_profile(site)
        if not profile or not profile.hr.enabled:
            logger.debug(f"站点 {site} 的 HR 监控未启用，跳过")
            return {"success": False, "reason": "not_enabled"}

        logger.info(f"LocalIntel: 开始处理站点 {site} 的 HR 页面")

        try:
            rows = await self.fetch_hr_rows(site, profile)
        except NotImplementedError:
            # 仍未实现 HTTP 抓取，给出友好日志
            logger.warning("HRWatcher.fetch_hr_rows 尚未实现，无法拉取真实 HR 数据")
            raise

        now = datetime.utcnow()
        seen_keys: set[Tuple[str, str]] = set()

        for row in rows:
            state = update_from_hr_page(
                site=site,
                torrent_id=row.torrent_id,
                required_seed_hours=row.required_seed_hours,
                seeded_hours=row.seeded_hours,
                deadline=row.deadline,
                now=now,
            )
            seen_keys.add((state.site, state.torrent_id))

        disappear_semantics = profile.hr.disappear_semantics.upper()
        for key, state in self._iter_site_states(site):
            if (state.site, state.torrent_id) in seen_keys:
                continue
            mark_from_hr_page_disappear(state, disappear_semantics, now=now)

        return {"success": True, "site": site, "rows": len(seen_keys)}

    async def refresh_site(self, site: str, profile: Optional[IntelSiteProfile] = None) -> Dict[str, Any]:
        """新增接口：执行抓取并同步仓库。"""
        result = await self.handle_site(site, profile=profile)
        if self._hr_repo and result.get("success"):
            for state in iter_site_states(site):
                await self._hr_repo.upsert(state)
        return result

    async def fetch_hr_rows(
        self,
        site: str,
        profile: IntelSiteProfile,
    ) -> Iterable[HRRow]:
        """抓取并解析 HR 页面。"""
        registry = get_http_client_registry()
        try:
            client = registry.get(site)
        except KeyError:
            logger.debug(f"LocalIntel: 未注册站点 {site} 的 HTTP 客户端，暂不抓取 HR")
            return []

        # 若站点未配置 HR 页面 URL，则直接返回
        if not profile.hr.hr_page_url and not profile.hr.mode:
            logger.debug(f"LocalIntel: 站点 {site} 未配置 HR 页面信息")
            return []

        html = await client.fetch_hr_page(profile)
        parser = HR_PARSERS.get(site, parse_hr_page_generic)
        parsed_rows: Iterable[ParsedHRRow] = parser(site=site, html=html, profile=profile)

        hr_rows: list[HRRow] = []
        for row in parsed_rows:
            required_hours = row.required_seed_hours if row.required_seed_hours is not None else 0.0
            seeded_hours = row.seeded_hours if row.seeded_hours is not None else 0.0
            hr_rows.append(
                HRRow(
                    torrent_id=row.torrent_id,
                    required_seed_hours=required_hours,
                    seeded_hours=seeded_hours,
                    deadline=row.deadline,
                )
            )
        return hr_rows

    def _iter_site_states(
        self,
        site: str,
    ) -> Iterable[Tuple[Tuple[str, str], HRTorrentState]]:
        """遍历该站点现有 HR 状态。"""
        for state in iter_site_states(site):
            yield (state.site, state.torrent_id), state

    async def handle_all_sites(self) -> Dict[str, Any]:
        """便利函数：遍历所有启用 HR 的站点。"""
        if not settings.INTEL_ENABLED or not settings.INTEL_HR_GUARD_ENABLED:
            logger.debug("LocalIntel HR Guard 未启用，跳过 HR 页面监控")
            return {"success": False, "reason": "not_enabled"}

        if not self._profiles:
            self.refresh_profiles()

        enabled_sites = [
            site for site, profile in self._profiles.items() if profile.hr.enabled
        ]
        if not enabled_sites:
            logger.debug("没有启用 HR 监控的站点")
            return {"success": True, "processed": 0}

        results = []
        for site in enabled_sites:
            try:
                result = await self.handle_site(site)
                results.append(result)
            except NotImplementedError:
                raise  # 交由调用方决策（目前 scheduler 会打日志）
            except Exception as exc:
                logger.error(f"处理站点 {site} HR 页面失败: {exc}", exc_info=True)
                results.append({"success": False, "site": site, "error": str(exc)})

        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "processed": len(results),
            "success_count": success_count,
            "results": results,
        }


# 全局单例
_hr_watcher: Optional[HRWatcher] = None


def get_hr_watcher() -> HRWatcher:
    """获取 HR Watcher 单例"""
    global _hr_watcher
    if _hr_watcher is None:
        _hr_watcher = HRWatcher()
    else:
        _hr_watcher.refresh_profiles()
    return _hr_watcher

