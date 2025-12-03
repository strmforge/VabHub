"""
VabHub Intel / Shared Intelligence 抽象层与基础实现

提供统一的别名识别、发布索引查询能力
支持本地、云端、混合三种模式
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, Optional

import asyncio
import json
from pathlib import Path

import httpx
from loguru import logger

from app.core.config import settings


class IntelResolveResult(Dict[str, Any]):
    """标准化后的作品信息结构（示意类型）。"""
    ...


class IntelReleaseSitesResult(Dict[str, Any]):
    """一个 release 在各站点的分布信息结构（示意类型）。"""
    ...


class IntelService(ABC):
    """Intel 抽象接口：提供统一的别名识别、发布索引查询能力。"""

    @abstractmethod
    async def resolve_title(self, raw_title: str) -> Optional[IntelResolveResult]:
        """输入原始标题 / 关键词，返回标准化作品信息（含 release_key、tmdb_id 等）。"""
        raise NotImplementedError

    @abstractmethod
    async def get_release_sites(self, release_key: str) -> IntelReleaseSitesResult:
        """输入 release_key，返回各站点分布信息（哪些 PT 站有这个资源）。"""
        raise NotImplementedError


class LocalIntelService(IntelService):
    """本地实现：使用 JSON/SQLite 存储的别名 & 索引。"""

    def __init__(self) -> None:
        self._loaded: bool = False
        self._aliases: Dict[str, IntelResolveResult] = {}
        self._index: Dict[str, IntelReleaseSitesResult] = {}

        # 计算数据目录路径（backend/data/intel）
        base_dir = Path(__file__).resolve().parents[3]  # backend 根
        self._data_dir = base_dir / "data" / "intel"
        self._aliases_file = self._data_dir / "aliases.json"
        self._index_file = self._data_dir / "index.json"

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"[LocalIntel] 创建数据目录失败: {e!r}")

        self._aliases = self._load_json_safe(self._aliases_file, default={})
        self._index = self._load_json_safe(self._index_file, default={})

        self._loaded = True
        logger.info(
            f"[LocalIntel] 本地别名/索引加载完成: aliases={len(self._aliases)}, index={len(self._index)}"
        )

    @staticmethod
    def _load_json_safe(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[LocalIntel] 加载 {path} 失败: {e!r}")
            return default

    async def resolve_title(self, raw_title: str) -> Optional[IntelResolveResult]:
        await self._ensure_loaded()

        key = raw_title.strip().lower()
        if not key:
            return None

        direct = self._aliases.get(key)
        if direct:
            return direct

        normalized_key = key.replace(" ", "")
        for alias_key, data in self._aliases.items():
            if alias_key.replace(" ", "") == normalized_key:
                return data

        return None

    async def get_release_sites(self, release_key: str) -> IntelReleaseSitesResult:
        await self._ensure_loaded()

        data = self._index.get(release_key)
        if data:
            return data

        return IntelReleaseSitesResult(
            release_key=release_key,
            sites=[],
        )


class CloudIntelService(IntelService):
    """云端实现：通过 https://intel.hbnetwork.top 请求共享智能中心。"""

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self._external_client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        return httpx.AsyncClient(timeout=5.0)

    async def resolve_title(self, raw_title: str) -> Optional[IntelResolveResult]:
        if not raw_title.strip():
            return None

        base_url = settings.INTEL_INTEL_ENDPOINT.rstrip("/")
        url = f"{base_url}/v1/alias/resolve"

        client = await self._get_client()
        try:
            resp = await client.get(url, params={"q": raw_title})
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            return IntelResolveResult(data)
        except httpx.HTTPError as e:
            logger.warning(f"[CloudIntel] resolve_title 调用失败: {e!r}")
            return None
        finally:
            if self._external_client is None:
                await client.aclose()

    async def get_release_sites(self, release_key: str) -> IntelReleaseSitesResult:
        base_url = settings.INTEL_INTEL_ENDPOINT.rstrip("/")
        url = f"{base_url}/v1/index/{release_key}"

        client = await self._get_client()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return IntelReleaseSitesResult(release_key=release_key, sites=[])
            return IntelReleaseSitesResult(data)
        except httpx.HTTPError as e:
            logger.warning(f"[CloudIntel] get_release_sites 调用失败: {e!r}")
            return IntelReleaseSitesResult(release_key=release_key, sites=[])
        finally:
            if self._external_client is None:
                await client.aclose()


class HybridIntelService(IntelService):
    """混合实现：云端优先，失败或超时回退本地。"""

    def __init__(self, local: LocalIntelService, cloud: CloudIntelService) -> None:
        self.local = local
        self.cloud = cloud

    async def resolve_title(self, raw_title: str) -> Optional[IntelResolveResult]:
        import asyncio as _asyncio
        
        # 优先尝试云端（带超时）
        cloud_task = _asyncio.create_task(self.cloud.resolve_title(raw_title))
        try:
            result = await _asyncio.wait_for(cloud_task, timeout=5.0)
            if result:
                logger.info(f"[HybridIntel] 云端 resolve_title 成功: {raw_title}")
                return result
        except _asyncio.TimeoutError:
            logger.warning(f"[HybridIntel] 云端 resolve_title 超时（5秒），回退本地: {raw_title}")
        except Exception as e:
            logger.warning(f"[HybridIntel] 云端 resolve_title 异常，回退本地: {e!r}")

        # 降级到本地
        if settings.INTEL_FALLBACK_TO_LOCAL:
            try:
                local_result = await self.local.resolve_title(raw_title)
                if local_result:
                    logger.info(f"[HybridIntel] 本地 resolve_title 成功: {raw_title}")
                return local_result
            except Exception as e:
                logger.error(f"[HybridIntel] 本地 resolve_title 也失败: {e!r}")

        return None

    async def get_release_sites(self, release_key: str) -> IntelReleaseSitesResult:
        import asyncio as _asyncio
        
        # 优先尝试云端（带超时）
        cloud_task = _asyncio.create_task(self.cloud.get_release_sites(release_key))
        try:
            result = await _asyncio.wait_for(cloud_task, timeout=5.0)
            if result and result.get("sites"):
                logger.info(f"[HybridIntel] 云端 get_release_sites 成功: {release_key}")
                return result
        except _asyncio.TimeoutError:
            logger.warning(f"[HybridIntel] 云端 get_release_sites 超时（5秒），回退本地: {release_key}")
        except Exception as e:
            logger.warning(f"[HybridIntel] 云端 get_release_sites 异常，回退本地: {e!r}")

        # 降级到本地
        if settings.INTEL_FALLBACK_TO_LOCAL:
            try:
                local_result = await self.local.get_release_sites(release_key)
                if local_result.get("sites"):
                    logger.info(f"[HybridIntel] 本地 get_release_sites 成功: {release_key}")
                return local_result
            except Exception as e:
                logger.error(f"[HybridIntel] 本地 get_release_sites 也失败: {e!r}")

        return IntelReleaseSitesResult(release_key=release_key, sites=[])


@lru_cache
def get_intel_service() -> IntelService:
    """根据配置构造全局单例 IntelService。"""
    local = LocalIntelService()
    cloud = CloudIntelService()

    if not settings.INTEL_ENABLED:
        logger.info("[Intel] INTEL_ENABLED=False，使用 LocalIntelService")
        return local

    mode = settings.INTEL_MODE.lower().strip()
    logger.info(f"[Intel] 初始化 IntelService，mode={mode}")

    if mode == "cloud":
        return cloud
    elif mode == "hybrid":
        return HybridIntelService(local=local, cloud=cloud)
    else:
        return local

