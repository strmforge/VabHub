"""
音乐下载调度 Runner

扫描状态为 found 的 MusicDownloadJob，获取下载链接并提交到下载器。

使用方式：
    python -m app.runners.music_download_dispatcher
    python -m app.runners.music_download_dispatcher --limit 50
    python -m app.runners.music_download_dispatcher --dry-run
    python -m app.runners.music_download_dispatcher --loop --loop-interval 300
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from loguru import logger


async def dispatch_downloads(
    limit: int = 50,
    dry_run: bool = False,
    client: str = "qbittorrent",
):
    """
    调度下载任务
    
    扫描 status=found 的 MusicDownloadJob，提交到下载器
    """
    from app.core.database import async_session_maker
    from app.models.music_download_job import MusicDownloadJob
    from app.services.music_indexer_service import get_music_indexer_service
    from sqlalchemy import select
    
    async with async_session_maker() as session:
        # 查询待下载的任务
        query = select(MusicDownloadJob).where(
            MusicDownloadJob.status == "found"
        ).order_by(
            MusicDownloadJob.quality_score.desc().nullslast(),
            MusicDownloadJob.created_at.asc()
        ).limit(limit)
        
        result = await session.execute(query)
        jobs = list(result.scalars().all())
        
        if not jobs:
            logger.info("没有待下载的任务")
            return {"dispatched": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"找到 {len(jobs)} 个待下载任务")
        
        stats = {"dispatched": 0, "failed": 0, "skipped": 0}
        indexer_service = get_music_indexer_service()
        
        for job in jobs:
            try:
                if dry_run:
                    logger.info(
                        f"[DRY-RUN] 将下载: {job.search_query} "
                        f"from {job.matched_site}:{job.matched_torrent_id}"
                    )
                    stats["dispatched"] += 1
                    continue
                
                # 获取下载链接
                download_link = await indexer_service.get_download_link(
                    job.matched_site,
                    job.matched_torrent_id,
                )
                
                if not download_link:
                    logger.warning(f"无法获取下载链接: {job.id}")
                    job.status = "failed"
                    job.last_error = "无法获取下载链接"
                    job.retry_count += 1
                    stats["failed"] += 1
                    continue
                
                # 调用下载服务
                download_result = await _submit_to_downloader(
                    session,
                    job,
                    download_link,
                    client,
                )
                
                if download_result.get("success"):
                    job.status = "submitted"
                    job.download_client = client
                    job.download_task_id = download_result.get("task_id")
                    job.downloader_hash = download_result.get("hash")
                    stats["dispatched"] += 1
                    
                    logger.info(
                        f"任务 {job.id} 已提交下载: {job.search_query}"
                    )
                else:
                    job.status = "failed"
                    job.last_error = download_result.get("error", "下载提交失败")
                    job.retry_count += 1
                    stats["failed"] += 1
                    
                    logger.error(
                        f"任务 {job.id} 下载提交失败: {download_result.get('error')}"
                    )
                
            except Exception as e:
                logger.error(f"处理任务 {job.id} 失败: {e}")
                job.status = "failed"
                job.last_error = str(e)
                job.retry_count += 1
                stats["failed"] += 1
        
        await session.commit()
        
        return stats


async def _submit_to_downloader(
    session,
    job: "MusicDownloadJob",
    download_link: str,
    client: str,
) -> dict:
    """
    提交到下载器
    
    复用现有的 DownloadService
    """
    try:
        from app.modules.download.service import DownloadService
        
        download_service = DownloadService(session)
        
        # 构造下载数据
        download_data = {
            "title": job.matched_torrent_name or job.search_query,
            "magnet_link": download_link if download_link.startswith("magnet:") else None,
            "torrent_url": download_link if not download_link.startswith("magnet:") else None,
            "size_gb": (job.matched_torrent_size_bytes or 0) / (1024 ** 3),
            "downloader": "qBittorrent" if client == "qbittorrent" else "Transmission",
            "media_type": "music",
            "extra_metadata": {
                "music_download_job_id": job.id,
                "source_site": job.matched_site,
                "source_torrent_id": job.matched_torrent_id,
            },
        }
        
        result = await download_service.create_download(download_data)
        
        if result.get("status") in ["downloading", "pending"]:
            return {
                "success": True,
                "task_id": result.get("id"),
                "hash": result.get("downloader_hash"),
            }
        else:
            return {
                "success": False,
                "error": f"下载状态异常: {result.get('status')}",
            }
            
    except Exception as e:
        logger.error(f"提交下载失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def main():
    parser = argparse.ArgumentParser(description='音乐下载调度工具')
    parser.add_argument('--limit', type=int, default=50, help='单次最多处理的任务数')
    parser.add_argument('--client', type=str, default='qbittorrent', 
                        choices=['qbittorrent', 'transmission'], help='下载器类型')
    parser.add_argument('--dry-run', action='store_true', help='只打印不执行')
    parser.add_argument('--loop', action='store_true', help='循环运行模式')
    parser.add_argument('--loop-interval', type=int, default=300, help='循环间隔（秒）')
    
    args = parser.parse_args()
    
    logger.info("音乐下载调度 Runner 启动")
    
    if args.loop:
        logger.info(f"循环模式，间隔 {args.loop_interval} 秒")
        while True:
            try:
                stats = await dispatch_downloads(
                    limit=args.limit,
                    dry_run=args.dry_run,
                    client=args.client,
                )
                print(f"\n调度完成: 提交={stats['dispatched']}, 失败={stats['failed']}")
            except Exception as e:
                logger.error(f"调度失败: {e}")
            
            logger.info(f"等待 {args.loop_interval} 秒后继续...")
            await asyncio.sleep(args.loop_interval)
    else:
        stats = await dispatch_downloads(
            limit=args.limit,
            dry_run=args.dry_run,
            client=args.client,
        )
        
        print("\n========== 下载调度统计 ==========")
        print(f"提交下载: {stats['dispatched']}")
        print(f"失败: {stats['failed']}")
        print("==================================\n")


if __name__ == '__main__':
    asyncio.run(main())
