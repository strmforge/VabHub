"""
OCR统计服务
用于记录和查询OCR识别历史、统计成功率等
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.models.ocr import OCRRecord


class OCRStatisticsService:
    """OCR统计服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_ocr_attempt(
        self,
        site_name: Optional[str] = None,
        site_url: Optional[str] = None,
        image_hash: Optional[str] = None,
        image_url: Optional[str] = None,
        original_text: Optional[str] = None,
        cleaned_text: Optional[str] = None,
        expected_length: Optional[int] = None,
        success: bool = False,
        confidence: Optional[float] = None,
        engine: Optional[str] = None,
        retry_count: int = 0,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> OCRRecord:
        """
        记录OCR识别尝试
        
        Returns:
            OCRRecord对象
        """
        try:
            record = OCRRecord(
                site_name=site_name,
                site_url=site_url,
                image_hash=image_hash,
                image_url=image_url,
                original_text=original_text,
                cleaned_text=cleaned_text,
                expected_length=expected_length,
                success=success,
                confidence=confidence,
                engine=engine,
                retry_count=retry_count,
                duration_ms=duration_ms,
                error_message=error_message
            )
            
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            
            return record
        except Exception as e:
            logger.error(f"记录OCR统计失败: {e}")
            await self.db.rollback()
            raise
    
    async def get_statistics(
        self,
        site_name: Optional[str] = None,
        engine: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取OCR统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 构建查询条件
            conditions = []
            if site_name:
                conditions.append(OCRRecord.site_name == site_name)
            if engine:
                conditions.append(OCRRecord.engine == engine)
            if start_date:
                conditions.append(OCRRecord.created_at >= start_date)
            if end_date:
                conditions.append(OCRRecord.created_at <= end_date)
            
            query = select(OCRRecord)
            if conditions:
                query = query.where(and_(*conditions))
            
            # 执行查询
            result = await self.db.execute(query)
            records = list(result.scalars().all())
            
            if not records:
                return {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0,
                    "avg_confidence": 0.0,
                    "by_site": {},
                    "by_engine": {}
                }
            
            # 计算统计信息
            total = len(records)
            success_count = sum(1 for r in records if r.success)
            failed_count = total - success_count
            success_rate = (success_count / total * 100) if total > 0 else 0.0
            
            # 平均耗时
            durations = [r.duration_ms for r in records if r.duration_ms is not None]
            avg_duration_ms = sum(durations) / len(durations) if durations else 0
            
            # 平均置信度
            confidences = [r.confidence for r in records if r.confidence is not None]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # 按站点统计
            by_site = {}
            for record in records:
                site = record.site_name or "unknown"
                if site not in by_site:
                    by_site[site] = {"total": 0, "success": 0, "failed": 0}
                by_site[site]["total"] += 1
                if record.success:
                    by_site[site]["success"] += 1
                else:
                    by_site[site]["failed"] += 1
            
            # 按引擎统计
            by_engine = {}
            for record in records:
                eng = record.engine or "unknown"
                if eng not in by_engine:
                    by_engine[eng] = {"total": 0, "success": 0, "failed": 0}
                by_engine[eng]["total"] += 1
                if record.success:
                    by_engine[eng]["success"] += 1
                else:
                    by_engine[eng]["failed"] += 1
            
            return {
                "total": total,
                "success": success_count,
                "failed": failed_count,
                "success_rate": round(success_rate, 2),
                "avg_duration_ms": round(avg_duration_ms, 2),
                "avg_confidence": round(avg_confidence, 2),
                "by_site": by_site,
                "by_engine": by_engine
            }
        except Exception as e:
            logger.error(f"获取OCR统计失败: {e}")
            raise
    
    async def get_recent_records(
        self,
        limit: int = 100,
        site_name: Optional[str] = None,
        success_only: Optional[bool] = None
    ) -> List[OCRRecord]:
        """
        获取最近的OCR记录
        
        Args:
            limit: 返回数量限制
            site_name: 站点名称过滤
            success_only: 是否只返回成功的记录
        
        Returns:
            OCR记录列表
        """
        try:
            query = select(OCRRecord).order_by(desc(OCRRecord.created_at))
            
            conditions = []
            if site_name:
                conditions.append(OCRRecord.site_name == site_name)
            if success_only is not None:
                conditions.append(OCRRecord.success == success_only)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取OCR记录失败: {e}")
            raise
    
    async def get_cached_result(self, image_hash: str) -> Optional[OCRRecord]:
        """
        从缓存中获取OCR结果（相同hash的图片）
        
        Args:
            image_hash: 图片MD5 hash
        
        Returns:
            OCRRecord对象，如果不存在返回None
        """
        try:
            query = select(OCRRecord).where(
                and_(
                    OCRRecord.image_hash == image_hash,
                    OCRRecord.success == True
                )
            ).order_by(desc(OCRRecord.created_at)).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取OCR缓存失败: {e}")
            return None
    
    async def cleanup_old_records(self, days: int = 30):
        """
        清理旧的OCR记录
        
        Args:
            days: 保留最近N天的记录
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            from sqlalchemy import delete
            query = delete(OCRRecord).where(OCRRecord.created_at < cutoff_date)
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"清理了 {deleted_count} 条旧的OCR记录（保留最近 {days} 天）")
            
            return deleted_count
        except Exception as e:
            logger.error(f"清理OCR记录失败: {e}")
            await self.db.rollback()
            raise
