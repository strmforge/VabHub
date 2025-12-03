"""
Demo 数据初始化 Runner
RELEASE-1 R3-2 实现

用法: python -m app.runners.demo_seed

在 Demo 模式下创建示例数据，供用户体验各模块功能。
"""

import asyncio
import sys
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings
from app.core.database import async_session_factory
from app.services.runner_heartbeat import runner_context


async def check_demo_mode():
    """检查是否为 Demo 模式"""
    if not settings.APP_DEMO_MODE:
        logger.warning("⚠️  当前不是 Demo 模式，demo_seed 不会执行")
        logger.warning("请设置 APP_DEMO_MODE=true 后重试")
        return False
    return True


async def seed_users(session):
    """创建 Demo 用户"""
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    # 检查是否已有用户
    result = await session.execute(select(User))
    if result.scalars().first():
        logger.info("用户已存在，跳过创建")
        return
    
    users = [
        User(
            username="admin",
            email="admin@demo.vabhub.local",
            hashed_password=get_password_hash("admin123"),
            full_name="管理员",
            is_superuser=True,
            role="admin",
        ),
        User(
            username="demo",
            email="demo@demo.vabhub.local",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo 用户",
            is_superuser=False,
            role="user",
        ),
    ]
    
    for user in users:
        session.add(user)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(users)} 个 Demo 用户")
    logger.info("   - admin / admin123 (管理员)")
    logger.info("   - demo / demo123 (普通用户)")


async def seed_ebooks(session):
    """创建 Demo 电子书/小说"""
    from app.models.ebook import EBook
    from sqlalchemy import select
    
    result = await session.execute(select(EBook).limit(1))
    if result.scalars().first():
        logger.info("电子书数据已存在，跳过创建")
        return
    
    ebooks = [
        EBook(
            title="三体",
            author="刘慈欣",
            description="文化大革命如火如荼进行的同时，军方探寻外星文明的绝秘计划「红岸工程」取得了突破性进展。",
            cover_url="/demo/covers/santi.jpg",
            file_path="/demo/ebooks/santi.epub",
            file_format="epub",
            total_chapters=100,
            status="completed",
        ),
        EBook(
            title="遮天",
            author="辰东",
            description="冰冷与黑暗并存的宇宙深处，九具庞大的龙尸拉着一口青铜古棺，亘古长存。",
            cover_url="/demo/covers/zhetian.jpg",
            file_path="/demo/ebooks/zhetian.txt",
            file_format="txt",
            total_chapters=2000,
            status="ongoing",
        ),
        EBook(
            title="斗破苍穹",
            author="天蚕土豆",
            description="这里是属于斗气的世界，没有花俏艳丽的魔法，有的，仅仅是繁衍到巅峰的斗气！",
            cover_url="/demo/covers/doupo.jpg",
            file_path="/demo/ebooks/doupo.txt",
            file_format="txt",
            total_chapters=1500,
            status="completed",
        ),
    ]
    
    for ebook in ebooks:
        session.add(ebook)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(ebooks)} 本 Demo 电子书")


async def seed_manga(session):
    """创建 Demo 漫画"""
    from app.models.manga import MangaSeries, MangaChapter
    from sqlalchemy import select
    
    result = await session.execute(select(MangaSeries).limit(1))
    if result.scalars().first():
        logger.info("漫画数据已存在，跳过创建")
        return
    
    manga_list = [
        {
            "title": "海贼王",
            "author": "尾田荣一郎",
            "description": "路飞的冒险故事",
            "cover_url": "/demo/covers/onepiece.jpg",
            "status": "ongoing",
            "chapters": 1100,
        },
        {
            "title": "鬼灭之刃",
            "author": "吾峠�的呼世晴",
            "description": "炭治郎的复仇之路",
            "cover_url": "/demo/covers/kimetsu.jpg",
            "status": "completed",
            "chapters": 205,
        },
        {
            "title": "咒术回战",
            "author": "芥见下々",
            "description": "虎杖悠仁的咒术世界",
            "cover_url": "/demo/covers/jujutsu.jpg",
            "status": "ongoing",
            "chapters": 250,
        },
    ]
    
    for manga_data in manga_list:
        series = MangaSeries(
            title=manga_data["title"],
            author=manga_data["author"],
            description=manga_data["description"],
            cover_url=manga_data["cover_url"],
            status=manga_data["status"],
            total_chapters=manga_data["chapters"],
        )
        session.add(series)
        await session.flush()
        
        # 创建前几章作为示例
        for i in range(1, min(6, manga_data["chapters"] + 1)):
            chapter = MangaChapter(
                series_id=series.id,
                chapter_number=i,
                title=f"第{i}话",
                page_count=20,
            )
            session.add(chapter)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(manga_list)} 个 Demo 漫画系列")


async def seed_music(session):
    """创建 Demo 音乐"""
    from app.models.music import Music, MusicFile
    from sqlalchemy import select
    
    result = await session.execute(select(Music).limit(1))
    if result.scalars().first():
        logger.info("音乐数据已存在，跳过创建")
        return
    
    music_list = [
        {
            "title": "晴天",
            "artist": "周杰伦",
            "album": "叶惠美",
            "duration": 269,
        },
        {
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "duration": 299,
        },
        {
            "title": "夜曲",
            "artist": "周杰伦",
            "album": "十一月的萧邦",
            "duration": 226,
        },
        {
            "title": "告白气球",
            "artist": "周杰伦",
            "album": "周杰伦的床边故事",
            "duration": 215,
        },
    ]
    
    for music_data in music_list:
        music = Music(
            title=music_data["title"],
            artist=music_data["artist"],
            album=music_data["album"],
            duration=music_data["duration"],
            cover_url=f"/demo/covers/music/{music_data['album']}.jpg",
        )
        session.add(music)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(music_list)} 首 Demo 音乐")


async def seed_tasks(session):
    """创建 Demo 任务记录"""
    from app.models.task import Task
    from sqlalchemy import select
    
    result = await session.execute(select(Task).limit(1))
    if result.scalars().first():
        logger.info("任务数据已存在，跳过创建")
        return
    
    tasks = [
        Task(
            task_type="download",
            title="[Demo] 下载任务示例 - 已完成",
            status="completed",
            progress=100,
            created_at=datetime.utcnow() - timedelta(hours=2),
        ),
        Task(
            task_type="download",
            title="[Demo] 下载任务示例 - 进行中",
            status="running",
            progress=45,
            created_at=datetime.utcnow() - timedelta(minutes=30),
        ),
        Task(
            task_type="tts",
            title="[Demo] TTS 生成任务 - 已完成",
            status="completed",
            progress=100,
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
        Task(
            task_type="sync",
            title="[Demo] 漫画同步任务 - 失败",
            status="failed",
            progress=0,
            error_message="Demo 模式下不执行真实同步",
            created_at=datetime.utcnow() - timedelta(hours=5),
        ),
    ]
    
    for task in tasks:
        session.add(task)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(tasks)} 个 Demo 任务记录")


async def main():
    """主函数"""
    async with runner_context("demo_seed", runner_type="manual"):
        logger.info("=" * 50)
        logger.info("VabHub Demo 数据初始化")
        logger.info("=" * 50)
        
        # 检查 Demo 模式
        if not await check_demo_mode():
            sys.exit(1)
        
        logger.info("🚀 开始创建 Demo 数据...")
        
        async with async_session_factory() as session:
            try:
                await seed_users(session)
                await seed_ebooks(session)
                await seed_manga(session)
                await seed_music(session)
                await seed_tasks(session)
                
                logger.info("=" * 50)
                logger.info("✅ Demo 数据初始化完成！")
                logger.info("=" * 50)
                logger.info("登录信息：")
                logger.info("  管理员: admin / admin123")
                logger.info("  普通用户: demo / demo123")
                
            except Exception as e:
                logger.error(f"❌ Demo 数据初始化失败: {e}")
                await session.rollback()
                raise


if __name__ == "__main__":
    asyncio.run(main())
