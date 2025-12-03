from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.download.service import DownloadService
from app.modules.music.schema_utils import ensure_music_schema
from app.modules.rsshub.schema_utils import ensure_subscription_health_columns
from app.modules.short_drama.schema_utils import ensure_short_drama_columns

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class SystemSelfCheckService:
    """聚合系统自检结果（依赖、schema、自测报告等）。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def gather(self) -> Dict[str, Any]:
        schema_checks = await self._run_schema_checks()
        optional_dependencies = await self._check_optional_dependencies()
        test_report = self._load_test_report()

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "optional_dependencies": optional_dependencies,
            "schema_checks": schema_checks,
            "test_report": test_report,
        }

    async def _check_optional_dependencies(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        redis_status = "disabled" if not settings.REDIS_ENABLED else "enabled"
        items.append(
            {
                "name": "Redis",
                "status": redis_status,
                "enabled": settings.REDIS_ENABLED,
                "message": "Redis 已关闭，缓存将退化为内存/L3" if not settings.REDIS_ENABLED else None,
                "details": {"url": settings.REDIS_URL},
            }
        )

        rsshub_status = "disabled" if not settings.RSSHUB_ENABLED else "enabled"
        items.append(
            {
                "name": "RSSHub",
                "status": rsshub_status,
                "enabled": settings.RSSHUB_ENABLED,
                "message": "RSSHub 已禁用，相关任务与自测会跳过" if not settings.RSSHUB_ENABLED else None,
                "details": {"base_url": settings.RSSHUB_BASE_URL},
            }
        )

        download_service = DownloadService(self.db)
        simulation_mode = await download_service.detect_simulation_mode()
        downloader_status = "simulation" if simulation_mode else "linked"
        items.append(
            {
                "name": "Downloader",
                "status": downloader_status,
                "enabled": not simulation_mode,
                "message": "当前未连接真实下载器，test_all 会跳过真实下载用例" if simulation_mode else None,
                "details": {"simulation_mode": simulation_mode},
            }
        )

        return items

    async def _run_schema_checks(self) -> Dict[str, Any]:
        steps_config = [
            ("short_drama_columns", "短剧相关列补齐", ensure_short_drama_columns, False),
            ("music_subscription_schema", "音乐订阅字段补齐", ensure_music_schema, False),
            ("rsshub_health_columns", "RSSHub 健康字段补齐", ensure_subscription_health_columns, True),
        ]

        steps: List[Dict[str, Any]] = []
        overall_status = "ok"

        for step_id, title, runner, needs_session in steps_config:
            started_at = datetime.utcnow().isoformat() + "Z"
            try:
                if needs_session:
                    await runner(self.db)
                else:
                    await runner()

                steps.append(
                    {
                        "id": step_id,
                        "title": title,
                        "status": "ok",
                        "started_at": started_at,
                        "finished_at": datetime.utcnow().isoformat() + "Z",
                    }
                )
            except Exception as exc:  # pragma: no cover - 防御性
                logger.warning(f"[selfcheck] {step_id} 自检失败: {exc}")
                steps.append(
                    {
                        "id": step_id,
                        "title": title,
                        "status": "error",
                        "error": str(exc),
                        "started_at": started_at,
                        "finished_at": datetime.utcnow().isoformat() + "Z",
                    }
                )
                overall_status = "error"

        return {
            "status": overall_status,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "steps": steps,
        }

    def _load_test_report(self) -> Dict[str, Any]:
        report_path = self._resolve_report_path()
        if not report_path.exists():
            return {
                "status": "missing",
                "path": str(report_path),
                "message": "未找到报告文件，请执行 test_all.py --report-path 保存最新结果",
            }

        try:
            with report_path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception as exc:  # pragma: no cover - 防御性
            logger.warning(f"[selfcheck] 读取测试报告失败: {exc}")
            return {
                "status": "error",
                "path": str(report_path),
                "message": f"读取失败: {exc}",
            }

        try:
            updated_at = datetime.utcfromtimestamp(report_path.stat().st_mtime).isoformat() + "Z"
        except Exception:  # pragma: no cover
            updated_at = None

        payload.setdefault("status", "ok")
        payload["path"] = str(report_path)
        payload["updated_at"] = updated_at
        return payload

    def _resolve_report_path(self) -> Path:
        raw_path = Path(settings.TEST_ALL_REPORT_PATH)
        if raw_path.is_absolute():
            return raw_path
        return (PROJECT_ROOT / raw_path).resolve()

