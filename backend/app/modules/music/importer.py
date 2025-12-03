"""
音乐入库服务

负责从下载完成的文件中识别音乐，并移动到统一的音乐库目录结构。
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.music import Music, MusicFile
from app.modules.music.work_resolver import MusicWorkResolver
from app.modules.media_renamer.category_helper import CategoryHelper
from app.modules.audiobook.media_info import probe_audio_file
from app.modules.inbox.models import InboxItem


# 支持的音乐文件格式
SUPPORTED_MUSIC_FORMATS = {".mp3", ".flac", ".ape", ".m4a", ".aac", ".ogg", ".wav", ".opus"}


class MusicImporter:
    """音乐入库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.library_root = Path(settings.MUSIC_LIBRARY_ROOT)
        self.library_root.mkdir(parents=True, exist_ok=True)
        self.work_resolver = MusicWorkResolver()
        self.category_helper = CategoryHelper()  # 用于二级分类
    
    @staticmethod
    def is_music_file(file_path: str) -> bool:
        """判断文件是否为支持的音乐格式"""
        path = Path(file_path)
        return path.suffix.lower() in SUPPORTED_MUSIC_FORMATS
    
    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        从文件名解析歌手、专辑、曲目等信息
        
        支持的格式示例：
        - "歌手 - 歌名.mp3"
        - "歌手 - 专辑 - 歌名.flac"
        - "歌手 - 专辑 - 01 - 歌名.mp3"
        - "歌手 - 专辑 - Disc1 - 01 - 歌名.flac"
        """
        path = Path(filename)
        stem = path.stem  # 不含扩展名的文件名
        
        # 尝试匹配 "歌手 - 专辑 - Disc1 - 01 - 歌名" 格式
        match = re.match(r"^(.+?)\s*-\s*(.+?)\s*-\s*Disc\s*(\d+)\s*-\s*(\d+)\s*-\s*(.+)$", stem, re.IGNORECASE)
        if match:
            artist, album, disc, track, title = match.groups()
            return {
                "artist": artist.strip(),
                "album": album.strip(),
                "disc_number": int(disc),
                "track_number": int(track),
                "title": title.strip(),
            }
        
        # 尝试匹配 "歌手 - 专辑 - 01 - 歌名" 格式
        match = re.match(r"^(.+?)\s*-\s*(.+?)\s*-\s*(\d+)\s*-\s*(.+)$", stem)
        if match:
            artist, album, track, title = match.groups()
            return {
                "artist": artist.strip(),
                "album": album.strip(),
                "track_number": int(track),
                "title": title.strip(),
            }
        
        # 尝试匹配 "歌手 - 专辑 - 歌名" 格式
        match = re.match(r"^(.+?)\s*-\s*(.+?)\s*-\s*(.+)$", stem)
        if match:
            artist, album, title = match.groups()
            return {
                "artist": artist.strip(),
                "album": album.strip(),
                "title": title.strip(),
            }
        
        # 尝试匹配 "歌手 - 歌名" 格式
        match = re.match(r"^(.+?)\s*-\s*(.+)$", stem)
        if match:
            artist, title = match.groups()
            return {
                "artist": artist.strip(),
                "title": title.strip(),
            }
        
        # 默认：整个文件名作为歌名
        return {
            "title": stem.strip(),
            "artist": None,
        }
    
    def parse_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        使用 mutagen 解析音频文件的元数据
        
        Returns:
            包含 artist, album, title, track_number, disc_number, genre, language 等的字典
        """
        metadata = {
            "artist": None,
            "album": None,
            "title": None,
            "album_artist": None,
            "track_number": None,
            "disc_number": None,
            "genre": None,
            "language": None,
            "year": None,
        }
        
        try:
            import mutagen
            from mutagen.id3 import ID3NoHeaderError
        except ImportError:
            logger.debug(f"mutagen 未安装，跳过音频元数据解析: {file_path}")
            return metadata
        
        try:
            audio = mutagen.File(str(file_path))
            if audio is None:
                logger.debug(f"无法识别音频文件格式: {file_path}")
                return metadata
            
            # 获取标签信息
            tags = audio.tags
            if not tags:
                logger.debug(f"音频文件没有标签信息: {file_path}")
                return metadata
            
            # 提取常见字段（支持多种标签格式）
            def get_tag_value(tag_key: str, fallback_keys: Optional[list] = None) -> Optional[str]:
                """获取标签值，支持多个键名"""
                keys_to_try = [tag_key]
                if fallback_keys:
                    keys_to_try.extend(fallback_keys)
                
                for key in keys_to_try:
                    if key in tags:
                        value = tags[key]
                        if isinstance(value, list) and len(value) > 0:
                            return str(value[0])
                        elif value:
                            return str(value)
                return None
            
            # 艺术家/歌手
            metadata["artist"] = get_tag_value("TPE1", ["ARTIST", "©ART", "artist"])
            metadata["album_artist"] = get_tag_value("TPE2", ["ALBUMARTIST", "album artist", "albumartist"])
            
            # 专辑
            metadata["album"] = get_tag_value("TALB", ["ALBUM", "©alb", "album"])
            
            # 标题
            metadata["title"] = get_tag_value("TIT2", ["TITLE", "©nam", "title"])
            
            # 轨道号
            track_str = get_tag_value("TRCK", ["TRACK", "track", "tracknumber"])
            if track_str:
                try:
                    # 可能是 "1/10" 格式，取第一部分
                    track_num = int(track_str.split("/")[0])
                    metadata["track_number"] = track_num
                except (ValueError, AttributeError):
                    pass
            
            # 碟号
            disc_str = get_tag_value("TPOS", ["DISC", "disc", "discnumber"])
            if disc_str:
                try:
                    disc_num = int(disc_str.split("/")[0])
                    metadata["disc_number"] = disc_num
                except (ValueError, AttributeError):
                    pass
            
            # 流派
            metadata["genre"] = get_tag_value("TCON", ["GENRE", "genre"])
            
            # 年份
            year_str = get_tag_value("TDRC", ["DATE", "YEAR", "year", "date"])
            if year_str:
                try:
                    # 提取年份（可能是 "2023" 或 "2023-01-01" 格式）
                    year = int(year_str.split("-")[0])
                    metadata["year"] = year
                except (ValueError, AttributeError):
                    pass
            
            # 语言（通常不在音频标签中，可能需要从其他来源获取）
            # 这里先留空，后续可以从 PT 分类或其他元数据中获取
            
            logger.debug(f"音频元数据解析成功: {file_path} - {metadata}")
            
        except Exception as e:
            logger.warning(f"解析音频文件元数据失败: {file_path}, 错误: {e}")
        
        return metadata
    
    def build_target_path(
        self,
        music: Music,
        music_file: MusicFile,
        category_subcategory: Optional[str] = None
    ) -> Path:
        """
        构建目标文件路径
        
        目录结构：
        - 如果命中分类：MUSIC_LIBRARY_ROOT/分类名/歌手/专辑/轨道号 - 歌名.ext
        - 如果未命中分类：MUSIC_LIBRARY_ROOT/歌手/专辑/轨道号 - 歌名.ext
        
        Args:
            music: Music 对象
            music_file: MusicFile 对象
            category_subcategory: 分类子目录名（可选）
        
        Returns:
            目标文件路径
        """
        # 清理文件名中的非法字符
        def clean_name(name: str) -> str:
            if not name:
                return "未知"
            illegal_chars = r'[<>:"/\\|?*]'
            return re.sub(illegal_chars, "_", name).strip()
        
        # 构建基础路径
        base_dir = self.library_root
        
        # 如果命中分类，在根目录下增加分类目录
        if category_subcategory:
            base_dir = base_dir / category_subcategory
        
        # 清理名称
        artist_clean = clean_name(music.artist) if music.artist else "未知歌手"
        album_clean = clean_name(music.album) if music.album else None
        title_clean = clean_name(music.title) if music.title else "未知曲目"
        
        # 确定文件格式
        file_format = music_file.format or "mp3"
        
        # 构建文件名
        if music_file.track_number is not None:
            filename = f"{music_file.track_number:02d} - {title_clean}.{file_format}"
        else:
            filename = f"{title_clean}.{file_format}"
        
        # 构建目录结构：歌手 / 专辑（如有）/ 文件名
        if album_clean:
            target_dir = base_dir / artist_clean / album_clean
        else:
            # 单曲，直接放在歌手目录下
            target_dir = base_dir / artist_clean / "单曲"
        
        return target_dir / filename
    
    async def import_music_from_path(
        self,
        file_path: Path,
        hints: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        从文件路径导入音乐
        
        Args:
            file_path: 源文件路径
            hints: 可选的提示信息（来自 InboxItem，可能包含 PT 分类等）
        
        Returns:
            成功时返回新路径，失败时返回 None
        """
        # 检查文件是否存在
        source_path = Path(file_path)
        if not source_path.exists() or not source_path.is_file():
            logger.warning(f"文件不存在或不是文件: {file_path}")
            return None
        
        # 检查文件格式
        if not self.is_music_file(str(file_path)):
            logger.debug(f"文件 {file_path} 不是支持的音乐格式")
            return None
        
        try:
            # 步骤 1: 解析音频元数据（使用 mutagen）
            audio_metadata = self.parse_audio_metadata(source_path)
            
            # 步骤 2: 如果元数据解析失败，尝试从文件名解析
            if not audio_metadata.get("artist") or not audio_metadata.get("title"):
                file_info = self.parse_filename(source_path.name)
                if not audio_metadata.get("artist"):
                    audio_metadata["artist"] = file_info.get("artist")
                if not audio_metadata.get("title"):
                    audio_metadata["title"] = file_info.get("title")
                if not audio_metadata.get("album"):
                    audio_metadata["album"] = file_info.get("album")
                if not audio_metadata.get("track_number"):
                    audio_metadata["track_number"] = file_info.get("track_number")
                if not audio_metadata.get("disc_number"):
                    audio_metadata["disc_number"] = file_info.get("disc_number")
            
            # 确保至少要有 artist 和 title
            if not audio_metadata.get("artist") or not audio_metadata.get("title"):
                logger.warning(f"无法从文件或文件名中解析出 artist 和 title: {file_path}")
                # 使用文件名作为兜底
                audio_metadata["title"] = audio_metadata.get("title") or source_path.stem
                audio_metadata["artist"] = audio_metadata.get("artist") or "未知歌手"
            
            # 从 hints 中提取额外信息（PT 分类、标签等）
            if hints:
                if "source_category" in hints:
                    # 可以从 PT 分类中推断语言等信息
                    pass
                if "source_tags" in hints:
                    # 可以从标签中提取信息
                    pass
            
            # 步骤 3: 获取音频技术信息（时长、码率等）
            audio_info = probe_audio_file(source_path)
            
            # 步骤 4: 使用 WorkResolver 查找已存在的作品
            existing_music = await self.work_resolver.find_existing_work(
                self.db,
                title=audio_metadata["title"],
                artist=audio_metadata["artist"],
                album=audio_metadata.get("album")
            )
            
            if existing_music:
                # 复用已存在的作品
                music = existing_music
                logger.info(f"找到已存在的作品，复用 Music: {music.id} - {music.artist} - {music.title}")
            else:
                # 创建新的作品记录
                # 构建 extra_metadata
                extra_metadata = {}
                if hints:
                    extra_metadata.update(hints)
                
                # 尝试从语言推断（如果有）
                language = audio_metadata.get("language")
                if not language:
                    # 可以从 artist 或 album 名称推断（简单启发式）
                    # 这里先留空，后续可以增强
                    pass
                
                music = Music(
                    title=audio_metadata["title"],
                    artist=audio_metadata["artist"],
                    album=audio_metadata.get("album"),
                    album_artist=audio_metadata.get("album_artist"),
                    genre=audio_metadata.get("genre"),
                    language=language,
                    year=audio_metadata.get("year"),
                    tags=None,  # 可以从 hints 中提取
                    extra_metadata=extra_metadata if extra_metadata else None
                )
                self.db.add(music)
                await self.db.flush()  # 获取 ID
                logger.info(f"创建新的作品记录: {music.id} - {music.artist} - {music.title}")
            
            # 步骤 5: 构建分类信息，用于目录分类
            music_info = {
                "original_language": music.language or audio_metadata.get("language"),
                "genre": music.genre,
                "tags": music.tags,
            }
            category_subcategory = self.category_helper.get_music_category(music_info)
            
            # 步骤 6: 构建目标路径
            # 先创建临时 music_file 用于传递格式信息
            file_size_bytes = source_path.stat().st_size
            file_format = source_path.suffix[1:].lower()  # 去掉点号
            
            temp_music_file = MusicFile(
                music_id=music.id,
                file_path="",  # 临时，稍后更新
                format=file_format,
                file_size_bytes=file_size_bytes,
                track_number=audio_metadata.get("track_number"),
                disc_number=audio_metadata.get("disc_number"),
                duration_seconds=audio_info.duration_seconds,
                bitrate_kbps=audio_info.bitrate_kbps,
                sample_rate_hz=audio_info.sample_rate_hz,
                channels=audio_info.channels,
            )
            target_path = self.build_target_path(music, temp_music_file, category_subcategory)
            
            # 如果目标文件已存在，生成唯一文件名
            if target_path.exists():
                base_path = target_path.parent / target_path.stem
                counter = 1
                while target_path.exists():
                    target_path = base_path.parent / f"{base_path.name} ({counter}){target_path.suffix}"
                    counter += 1
            
            # 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件（在数据库操作之前完成文件操作）
            shutil.move(str(source_path), str(target_path))
            logger.info(f"音乐文件已移动: {source_path} -> {target_path}")
            
            # 步骤 7: 创建音乐文件记录
            music_file = MusicFile(
                music_id=music.id,
                file_path=str(target_path),
                file_size_bytes=file_size_bytes,
                format=file_format,
                track_number=audio_metadata.get("track_number"),
                disc_number=audio_metadata.get("disc_number"),
                duration_seconds=audio_info.duration_seconds,
                bitrate_kbps=audio_info.bitrate_kbps,
                sample_rate_hz=audio_info.sample_rate_hz,
                channels=audio_info.channels,
                source_site_id=str(hints.get("source_site_id")) if hints and hints.get("source_site_id") else None,
                source_torrent_id=hints.get("source_torrent_id") if hints else None,
                download_task_id=hints.get("download_task_id") if hints else None,
            )
            self.db.add(music_file)
            await self.db.commit()
            
            logger.info(f"音乐导入成功: {music.artist} - {music.title} -> {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"导入音乐失败: {file_path}, 错误: {e}", exc_info=True)
            await self.db.rollback()
            return None

