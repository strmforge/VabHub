from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WorkerRegisterRequest(BaseModel):
    node_id: str
    capabilities: Dict[str, Any]


class WorkerRegisterResponse(BaseModel):
    ok: bool = True


class JobLeaseRequest(BaseModel):
    node_id: str
    want_sites: Optional[List[str]] = None
    max_jobs: int = 1


class JobPayload(BaseModel):
    id: int
    site_id: str
    payload: Dict[str, Any]


class JobLeaseResponse(BaseModel):
    jobs: List[JobPayload] = []


class JobFinishRequest(BaseModel):
    job_id: int
    node_id: str
    success: bool
    error_message: Optional[str] = None
    new_cursor_value: Optional[str] = None

