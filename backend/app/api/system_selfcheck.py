from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.schemas import BaseResponse, success_response
from app.modules.system_selfcheck.service import SystemSelfCheckService

router = APIRouter()


@router.get("/selfcheck", response_model=BaseResponse)
async def get_system_selfcheck(db: AsyncSession = Depends(get_db)):
    service = SystemSelfCheckService(db)
    result = await service.gather()
    return success_response(data=result, message="系统自检结果")

