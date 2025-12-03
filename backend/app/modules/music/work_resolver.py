"""
音乐作品解析器

负责查找或创建 Music 作品记录，确保同一作品不会重复创建。
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from loguru import logger

from app.models.music import Music


class MusicWorkResolver:
    """
    音乐作品解析器
    
    用于查找已存在的音乐作品，避免重复创建。
    """
    
    @staticmethod
    def _normalize_string(s: Optional[str]) -> Optional[str]:
        """规范化字符串（去除空格、转小写）"""
        if not s:
            return None
        return s.strip().lower()
    
    async def find_existing_work(
        self,
        db: AsyncSession,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[Music]:
        """
        查找已存在的音乐作品
        
        Args:
            db: 数据库会话
            title: 曲目标题
            artist: 艺术家/歌手
            album: 专辑名（可选）
        
        Returns:
            如果找到已存在的作品，返回 Music 对象；否则返回 None
        """
        if not title or not artist:
            return None
        
        # 规范化输入
        normalized_title = self._normalize_string(title)
        normalized_artist = self._normalize_string(artist)
        normalized_album = self._normalize_string(album)
        
        # 构建查询条件
        conditions = []
        
        # 标题和艺术家必须匹配
        conditions.append(Music.title.ilike(f"%{normalized_title}%"))
        conditions.append(Music.artist.ilike(f"%{normalized_artist}%"))
        
        # 如果有专辑，尝试匹配专辑
        if normalized_album:
            conditions.append(
                or_(
                    Music.album.ilike(f"%{normalized_album}%"),
                    Music.album.is_(None)  # 也允许专辑为空的记录（单曲）
                )
            )
        
        # 执行查询
        stmt = select(Music).where(and_(*conditions))
        result = await db.execute(stmt)
        existing_music = result.scalar_one_or_none()
        
        if existing_music:
            logger.debug(f"找到已存在的音乐作品: {existing_music.id} - {existing_music.artist} - {existing_music.title}")
        
        return existing_music

