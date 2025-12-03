"""
音乐导入服务

负责将下载完成的音乐文件导入到本地音乐库。
支持：
- 解析音频文件元数据（使用 mutagen）
- 创建/更新 Music 和 MusicFile 记录
- 去重检测和质量优选

使用方式：
    from app.services.music_import_service import import_music_from_path
    
    result = await import_music_from_path(session, "/path/to/music.flac")
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.music import Music, MusicFile
from app.models.music_download_job import MusicDownloadJob


@dataclass
class ParsedMusicMeta:
    """解析后的音乐元数据"""
    title: str
    artist: str
    album: Optional[str] = None
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    
    # 音频质量信息
    format: str = "unknown"
    bitrate_kbps: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    
    # 文件信息
    file_size_bytes: Optional[int] = None


@dataclass
class MusicImportResult:
    """导入结果"""
    success: bool
    music_id: Optional[int] = None
    file_id: Optional[int] = None
    is_duplicate: bool = False
    is_quality_upgrade: bool = False
    message: str = ""
    error: Optional[str] = None


# 格式优先级（用于质量比较）
FORMAT_PRIORITY = {
    "flac": 100,
    "ape": 95,
    "wav": 90,
    "alac": 85,
    "aac": 70,
    "m4a": 65,
    "ogg": 60,
    "mp3": 50,
}


def parse_audio_file(file_path: str) -> Optional[ParsedMusicMeta]:
    """
    解析音频文件元数据
    
    使用 mutagen 库解析各种音频格式
    """
    try:
        import mutagen
        from mutagen.easyid3 import EasyID3
        from mutagen.flac import FLAC
        from mutagen.mp3 import MP3
        from mutagen.mp4 import MP4
        from mutagen.oggvorbis import OggVorbis
        from mutagen.apev2 import APEv2
    except ImportError:
        logger.warning("mutagen 库未安装，无法解析音频元数据")
        return None
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    try:
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        ext = Path(file_path).suffix.lower().lstrip(".")
        
        # 尝试解析
        audio = mutagen.File(file_path, easy=True)
        
        if audio is None:
            logger.warning(f"无法解析音频文件: {file_path}")
            return None
        
        # 提取基本信息
        title = _get_tag(audio, ["title"]) or Path(file_path).stem
        artist = _get_tag(audio, ["artist", "albumartist"]) or "Unknown Artist"
        album = _get_tag(audio, ["album"])
        album_artist = _get_tag(audio, ["albumartist"])
        genre = _get_tag(audio, ["genre"])
        
        # 年份
        year = None
        year_str = _get_tag(audio, ["date", "year"])
        if year_str:
            try:
                year = int(year_str[:4])
            except (ValueError, TypeError):
                pass
        
        # 轨道号
        track_number = None
        track_str = _get_tag(audio, ["tracknumber"])
        if track_str:
            try:
                track_number = int(track_str.split("/")[0])
            except (ValueError, TypeError):
                pass
        
        # 碟号
        disc_number = None
        disc_str = _get_tag(audio, ["discnumber"])
        if disc_str:
            try:
                disc_number = int(disc_str.split("/")[0])
            except (ValueError, TypeError):
                pass
        
        # 时长
        duration_seconds = None
        if hasattr(audio, "info") and audio.info:
            duration_seconds = int(audio.info.length) if audio.info.length else None
        
        # 音频质量信息
        bitrate_kbps = None
        sample_rate_hz = None
        channels = None
        bit_depth = None
        
        if hasattr(audio, "info") and audio.info:
            info = audio.info
            
            if hasattr(info, "bitrate"):
                bitrate_kbps = int(info.bitrate / 1000) if info.bitrate else None
            
            if hasattr(info, "sample_rate"):
                sample_rate_hz = info.sample_rate
            
            if hasattr(info, "channels"):
                channels = info.channels
            
            if hasattr(info, "bits_per_sample"):
                bit_depth = info.bits_per_sample
        
        return ParsedMusicMeta(
            title=title,
            artist=artist,
            album=album,
            album_artist=album_artist,
            genre=genre,
            year=year,
            track_number=track_number,
            disc_number=disc_number,
            duration_seconds=duration_seconds,
            format=ext,
            bitrate_kbps=bitrate_kbps,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
            bit_depth=bit_depth,
            file_size_bytes=file_size,
        )
        
    except Exception as e:
        logger.error(f"解析音频文件失败 {file_path}: {e}")
        return None


def _get_tag(audio, keys: List[str]) -> Optional[str]:
    """从音频对象获取标签值"""
    for key in keys:
        try:
            value = audio.get(key)
            if value:
                if isinstance(value, list):
                    return str(value[0]) if value else None
                return str(value)
        except:
            pass
    return None


def calculate_quality_score(meta: ParsedMusicMeta) -> float:
    """
    计算音频质量评分
    
    用于比较同一曲目的不同版本
    """
    score = 0.0
    
    # 格式分数（0-100）
    score += FORMAT_PRIORITY.get(meta.format.lower(), 30)
    
    # 比特率分数（0-50）
    if meta.bitrate_kbps:
        if meta.bitrate_kbps >= 1000:  # 无损
            score += 50
        elif meta.bitrate_kbps >= 320:
            score += 40
        elif meta.bitrate_kbps >= 256:
            score += 30
        elif meta.bitrate_kbps >= 192:
            score += 20
        else:
            score += 10
    
    # 采样率分数（0-20）
    if meta.sample_rate_hz:
        if meta.sample_rate_hz >= 96000:
            score += 20
        elif meta.sample_rate_hz >= 48000:
            score += 15
        elif meta.sample_rate_hz >= 44100:
            score += 10
    
    # 位深分数（0-20）
    if meta.bit_depth:
        if meta.bit_depth >= 24:
            score += 20
        elif meta.bit_depth >= 16:
            score += 10
    
    return round(score, 2)


async def find_existing_music(
    session: AsyncSession,
    meta: ParsedMusicMeta,
) -> Optional[Music]:
    """
    查找已存在的 Music 记录
    
    匹配条件：
    - 艺术家名称相似
    - 标题相似
    - 专辑名称相似（如果有）
    """
    # 标准化名称
    def normalize(s: str) -> str:
        if not s:
            return ""
        return s.lower().strip()
    
    artist_norm = normalize(meta.artist)
    title_norm = normalize(meta.title)
    
    # 精确匹配
    query = select(Music).where(
        and_(
            func.lower(Music.artist) == artist_norm,
            func.lower(Music.title) == title_norm,
        )
    )
    
    if meta.album:
        query = query.where(func.lower(Music.album) == normalize(meta.album))
    
    result = await session.execute(query)
    music = result.scalar_one_or_none()
    
    return music


async def find_existing_file(
    session: AsyncSession,
    file_path: str,
) -> Optional[MusicFile]:
    """查找已存在的文件记录"""
    result = await session.execute(
        select(MusicFile).where(MusicFile.file_path == file_path)
    )
    return result.scalar_one_or_none()


async def import_music_from_path(
    session: AsyncSession,
    file_path: str,
    *,
    source_site_id: Optional[str] = None,
    source_torrent_id: Optional[str] = None,
    download_job_id: Optional[int] = None,
) -> MusicImportResult:
    """
    从文件路径导入音乐
    
    Args:
        session: 数据库会话
        file_path: 音频文件路径
        source_site_id: 来源站点 ID
        source_torrent_id: 来源种子 ID
        download_job_id: 关联的下载任务 ID
        
    Returns:
        导入结果
    """
    # 检查文件是否已存在
    existing_file = await find_existing_file(session, file_path)
    if existing_file:
        return MusicImportResult(
            success=True,
            music_id=existing_file.music_id,
            file_id=existing_file.id,
            is_duplicate=True,
            message="文件已存在",
        )
    
    # 解析元数据
    meta = parse_audio_file(file_path)
    if not meta:
        return MusicImportResult(
            success=False,
            error="无法解析音频文件元数据",
        )
    
    # 计算质量评分
    quality_score = calculate_quality_score(meta)
    
    # 查找已存在的 Music
    existing_music = await find_existing_music(session, meta)
    
    is_duplicate = False
    is_quality_upgrade = False
    
    if existing_music:
        # 检查是否有更好的版本
        existing_files_result = await session.execute(
            select(MusicFile).where(
                and_(
                    MusicFile.music_id == existing_music.id,
                    MusicFile.is_preferred == True,
                )
            )
        )
        existing_preferred = existing_files_result.scalar_one_or_none()
        
        if existing_preferred:
            existing_score = existing_preferred.quality_score or 0
            
            if quality_score > existing_score:
                # 新文件质量更好，升级
                is_quality_upgrade = True
                existing_preferred.is_preferred = False
                logger.info(
                    f"质量升级: {meta.title} "
                    f"({existing_score} -> {quality_score})"
                )
            else:
                # 新文件质量不如已有版本
                is_duplicate = True
                logger.info(
                    f"跳过低质量版本: {meta.title} "
                    f"(new={quality_score}, existing={existing_score})"
                )
        
        music = existing_music
    else:
        # 创建新的 Music 记录
        music = Music(
            title=meta.title,
            artist=meta.artist,
            album=meta.album,
            album_artist=meta.album_artist,
            genre=meta.genre,
            year=meta.year,
        )
        session.add(music)
        await session.flush()
    
    # 创建 MusicFile 记录
    music_file = MusicFile(
        music_id=music.id,
        file_path=file_path,
        file_size_bytes=meta.file_size_bytes,
        format=meta.format,
        duration_seconds=meta.duration_seconds,
        bitrate_kbps=meta.bitrate_kbps,
        sample_rate_hz=meta.sample_rate_hz,
        channels=meta.channels,
        bit_depth=meta.bit_depth,
        track_number=meta.track_number,
        disc_number=meta.disc_number,
        source_site_id=source_site_id,
        source_torrent_id=source_torrent_id,
        download_job_id=download_job_id,
        is_preferred=not is_duplicate,
        quality_score=quality_score,
    )
    session.add(music_file)
    await session.flush()
    
    return MusicImportResult(
        success=True,
        music_id=music.id,
        file_id=music_file.id,
        is_duplicate=is_duplicate,
        is_quality_upgrade=is_quality_upgrade,
        message="导入成功" if not is_duplicate else "已有更好版本",
    )


async def import_music_from_download_job(
    session: AsyncSession,
    job: MusicDownloadJob,
    task: Any,  # DownloadTask
) -> dict:
    """
    从下载任务导入音乐
    
    扫描下载目录，导入所有音频文件
    """
    # 获取下载路径
    download_path = getattr(task, "save_path", None) or job.downloaded_path
    
    if not download_path:
        return {
            "success": False,
            "error": "无法获取下载路径",
        }
    
    # 支持的音频格式
    audio_extensions = {".mp3", ".flac", ".ape", ".wav", ".m4a", ".aac", ".ogg", ".wma"}
    
    # 扫描目录或单文件
    files_to_import = []
    
    if os.path.isfile(download_path):
        if Path(download_path).suffix.lower() in audio_extensions:
            files_to_import.append(download_path)
    elif os.path.isdir(download_path):
        for root, dirs, files in os.walk(download_path):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    files_to_import.append(os.path.join(root, file))
    
    if not files_to_import:
        return {
            "success": False,
            "error": f"未找到音频文件: {download_path}",
        }
    
    # 导入所有文件
    imported_count = 0
    first_result = None
    
    for file_path in files_to_import:
        result = await import_music_from_path(
            session,
            file_path,
            source_site_id=job.matched_site,
            source_torrent_id=job.matched_torrent_id,
            download_job_id=job.id,
        )
        
        if result.success:
            imported_count += 1
            if first_result is None:
                first_result = result
    
    if imported_count > 0:
        return {
            "success": True,
            "file_id": first_result.file_id if first_result else None,
            "music_id": first_result.music_id if first_result else None,
            "is_duplicate": first_result.is_duplicate if first_result else False,
            "imported_count": imported_count,
            "message": f"成功导入 {imported_count} 个文件",
        }
    else:
        return {
            "success": False,
            "error": "所有文件导入失败",
        }
