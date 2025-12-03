from typing import List
import json
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import Base, engine, get_session
from .models import Job, SiteCursor, Worker
from .schemas import (
    JobFinishRequest,
    JobLeaseRequest,
    JobLeaseResponse,
    JobPayload,
    WorkerRegisterRequest,
    WorkerRegisterResponse,
)


app = FastAPI(title="VabHub Mesh Scheduler")


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Mesh Scheduler DB 初始化完成")


async def verify_network_key(
    x_network_key: str = Header(..., alias="X-Network-Key"),
) -> None:
    if x_network_key != settings.NETWORK_SHARED_KEY:
        raise HTTPException(status_code=401, detail="Invalid network key")


@app.post(
    "/v1/worker/register",
    response_model=WorkerRegisterResponse,
    dependencies=[Depends(verify_network_key)],
)
async def register_worker(
    payload: WorkerRegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> WorkerRegisterResponse:
    q = select(Worker).where(Worker.node_id == payload.node_id)
    result = await session.execute(q)
    worker = result.scalar_one_or_none()

    if worker is None:
        worker = Worker(
            node_id=payload.node_id,
            capabilities=str(payload.capabilities or {}),
        )
        session.add(worker)
    else:
        worker.capabilities = str(payload.capabilities or {})
        worker.is_active = True

    await session.commit()
    logger.info(f"[Mesh] worker 注册/更新: node_id={payload.node_id}")
    return WorkerRegisterResponse(ok=True)


@app.post(
    "/v1/jobs/lease",
    response_model=JobLeaseResponse,
    dependencies=[Depends(verify_network_key)],
)
async def lease_jobs(
    payload: JobLeaseRequest,
    session: AsyncSession = Depends(get_session),
) -> JobLeaseResponse:
    q = select(Job).where(Job.status == "pending")
    if payload.want_sites:
        q = q.where(Job.site_id.in_(payload.want_sites))

    q = q.limit(payload.max_jobs)
    result = await session.execute(q)
    jobs: List[Job] = list(result.scalars().all())

    leased_jobs: List[JobPayload] = []

    for job in jobs:
        job.status = "leased"
        job.leased_by = payload.node_id
        job.leased_at = datetime.utcnow()
        payload_data = {}
        if job.payload:
            try:
                payload_data = json.loads(job.payload)
            except json.JSONDecodeError:
                logger.warning(f"[Mesh] 解析job payload失败: job_id={job.id}")
        
        leased_jobs.append(
            JobPayload(
                id=job.id,
                site_id=job.site_id,
                payload=payload_data,
            )
        )

    await session.commit()
    logger.info(f"[Mesh] worker={payload.node_id} lease jobs count={len(leased_jobs)}")
    return JobLeaseResponse(jobs=leased_jobs)


@app.post("/v1/jobs/finish", dependencies=[Depends(verify_network_key)])
async def finish_job(
    payload: JobFinishRequest,
    session: AsyncSession = Depends(get_session),
):
    q = select(Job).where(Job.id == payload.job_id)
    result = await session.execute(q)
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "done" if payload.success else "failed"
    job.updated_at = datetime.utcnow()

    if payload.new_cursor_value:
        cq = select(SiteCursor).where(SiteCursor.site_id == job.site_id)
        cr = await session.execute(cq)
        cursor = cr.scalar_one_or_none()
        if cursor is None:
            cursor = SiteCursor(site_id=job.site_id, cursor_value=payload.new_cursor_value)
            session.add(cursor)
        else:
            cursor.cursor_value = payload.new_cursor_value
        logger.info(f"[Mesh] 更新 site cursor: site={job.site_id}, cursor={payload.new_cursor_value}")

    await session.commit()
    logger.info(f"[Mesh] job 完成: id={payload.job_id}, success={payload.success}")
    return {"ok": True}

