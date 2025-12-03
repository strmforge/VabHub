from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.intel_local import (
    LocalIntelEngine,
    get_site_profile,
)


router = APIRouter(prefix="/admin/local-intel", tags=["admin-local-intel"])


def get_local_intel_engine(request: Request) -> LocalIntelEngine:
    engine = getattr(request.app.state, "local_intel_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Local Intel Engine 未初始化")
    return engine


def _serialize_payload(payload: dict | None) -> dict | None:
    if not payload:
        return None

    def convert(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return {k: convert(v) for k, v in payload.items()}


@router.post("/refresh/{site_id}")
async def admin_refresh_local_intel(
    site_id: str,
    request: Request,
    engine: LocalIntelEngine = Depends(get_local_intel_engine),
):
    profile = get_site_profile(site_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 未找到配置")

    actions = await engine.refresh_site(site_id, profile)
    return {
        "site": site_id,
        "actions": [
            {
                "type": action.type.value,
                "site": action.site,
                "torrent_id": action.torrent_id,
                "title": action.title,
                "message": action.message,
                "level": action.level,
                "payload": _serialize_payload(action.payload),
                "created_at": action.created_at.isoformat() if action.created_at else None,
            }
            for action in actions
        ],
    }

