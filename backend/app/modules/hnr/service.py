"""
HNR检测服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import json

from app.models.hnr import HNRDetection, HNRTask, HNRSignature
from app.models.download import DownloadTask
from app.modules.hnr.detector import HNRDetector, HNRVerdict
from app.core.config import settings


class HNRService:
    """HNR检测服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # 使用配置中的签名包路径
        pack_path = settings.HNR_SIGNATURE_PACK_PATH
        self.detector = HNRDetector(signature_pack_path=pack_path if pack_path else None)
    
    def reload_signatures(self) -> bool:
        """重新加载签名包（热更新）"""
        return self.detector.reload_signatures()
    
    async def detect_hnr(
        self,
        title: str,
        subtitle: str = "",
        badges_text: str = "",
        list_html: str = "",
        site_id: Optional[int] = None,
        site_name: Optional[str] = None,
        download_task_id: Optional[int] = None
    ) -> HNRDetection:
        """执行HNR检测"""
        # 执行检测
        result = self.detector.detect(
            title=title,
            subtitle=subtitle,
            badges_text=badges_text,
            list_html=list_html,
            site_id=str(site_id) if site_id else None
        )
        
        # 保存检测记录
        detection = HNRDetection(
            download_task_id=download_task_id,
            title=title,
            site_id=site_id,
            site_name=site_name,
            verdict=result.verdict.value,
            confidence=result.confidence,
            matched_rules=json.dumps(result.matched_rules),
            category=result.category,
            penalties=json.dumps(result.penalties),
            message=result.message,
            detected_at=datetime.utcnow()
        )
        
        self.db.add(detection)
        await self.db.commit()
        await self.db.refresh(detection)
        
        logger.info(f"HNR检测完成: {title} - {result.verdict.value} (置信度: {result.confidence})")
        
        return detection
    
    async def create_monitoring_task(
        self,
        download_task_id: int,
        title: str,
        site_id: Optional[int] = None,
        site_name: Optional[str] = None,
        required_ratio: float = 1.0,
        required_seed_time_hours: float = 0.0
    ) -> HNRTask:
        """创建HNR监控任务"""
        # 检查是否已存在
        existing = await self.get_task_by_download_id(download_task_id)
        if existing:
            return existing
        
        task = HNRTask(
            download_task_id=download_task_id,
            title=title,
            site_id=site_id,
            site_name=site_name,
            status="monitoring",
            risk_score=0.0,
            current_ratio=0.0,
            required_ratio=required_ratio,
            seed_time_hours=0.0,
            required_seed_time_hours=required_seed_time_hours,
            downloaded_gb=0.0,
            uploaded_gb=0.0,
            last_check=None,
            next_check=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        logger.info(f"HNR监控任务已创建: {title} (下载任务ID: {download_task_id})")
        
        return task
    
    async def get_task_by_download_id(self, download_task_id: int) -> Optional[HNRTask]:
        """根据下载任务ID获取监控任务"""
        result = await self.db.execute(
            select(HNRTask).where(HNRTask.download_task_id == download_task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_task(self, task_id: int) -> Optional[HNRTask]:
        """获取监控任务"""
        result = await self.db.execute(
            select(HNRTask).where(HNRTask.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        site_id: Optional[int] = None
    ) -> List[HNRTask]:
        """获取监控任务列表"""
        query = select(HNRTask)
        
        conditions = []
        if status:
            conditions.append(HNRTask.status == status)
        if min_risk_score is not None:
            conditions.append(HNRTask.risk_score >= min_risk_score)
        if site_id:
            conditions.append(HNRTask.site_id == site_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(HNRTask.risk_score.desc(), HNRTask.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_task_metrics(
        self,
        task_id: int,
        current_ratio: Optional[float] = None,
        seed_time_hours: Optional[float] = None,
        downloaded_gb: Optional[float] = None,
        uploaded_gb: Optional[float] = None
    ) -> Optional[HNRTask]:
        """更新任务指标"""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        if current_ratio is not None:
            task.current_ratio = current_ratio
        if seed_time_hours is not None:
            task.seed_time_hours = seed_time_hours
        if downloaded_gb is not None:
            task.downloaded_gb = downloaded_gb
        if uploaded_gb is not None:
            task.uploaded_gb = uploaded_gb
        
        # 重新计算风险评分
        task.risk_score = self.detector.calculate_risk_score(
            current_ratio=task.current_ratio,
            required_ratio=task.required_ratio,
            seed_time_hours=task.seed_time_hours,
            required_seed_time_hours=task.required_seed_time_hours
        )
        
        task.last_check = datetime.utcnow()
        task.next_check = datetime.utcnow() + timedelta(hours=1)
        task.updated_at = datetime.utcnow()
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        return task
    
    async def get_risk_stats(self) -> Dict[str, int]:
        """获取风险统计"""
        result = await self.db.execute(
            select(
                func.count(HNRTask.id).label('total'),
                func.sum(func.case((HNRTask.risk_score >= 0.7, 1), else_=0)).label('high'),
                func.sum(func.case((and_(HNRTask.risk_score >= 0.3, HNRTask.risk_score < 0.7), 1), else_=0)).label('medium'),
                func.sum(func.case((HNRTask.risk_score < 0.3, 1), else_=0)).label('low')
            ).where(HNRTask.status == "monitoring")
        )
        stats = result.first()
        
        return {
            "total": stats.total or 0,
            "high": stats.high or 0,
            "medium": stats.medium or 0,
            "low": stats.low or 0
        }
    
    async def get_recent_detections(
        self,
        limit: int = 20,
        verdict: Optional[str] = None
    ) -> List[HNRDetection]:
        """获取最近的检测记录"""
        query = select(HNRDetection).order_by(HNRDetection.detected_at.desc()).limit(limit)
        
        if verdict:
            query = query.where(HNRDetection.verdict == verdict)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_task(self, task_id: int) -> bool:
        """删除监控任务"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await self.db.delete(task)
        await self.db.commit()
        return True

