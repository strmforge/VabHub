"""
音乐导入 Runner

从指定目录扫描音乐文件并导入到数据库。

使用方式：
    python -m app.runners.music_import --root /path/to/music
    python -m app.runners.music_import --root /path/to/music --dry-run
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from loguru import logger


# 支持的音频格式
SUPPORTED_FORMATS = {'.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wav', '.ape', '.wma'}


def parse_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    从文件名解析艺术家和标题
    
    支持的格式：
    - "艺术家 - 歌曲名.mp3"
    - "歌曲名.mp3"（艺术家为 Unknown）
    """
    name = Path(filename).stem
    
    # 尝试按 " - " 分割
    if ' - ' in name:
        parts = name.split(' - ', 1)
        return {
            'artist': parts[0].strip(),
            'title': parts[1].strip()
        }
    
    # 尝试按 "-" 分割
    if '-' in name:
        parts = name.split('-', 1)
        return {
            'artist': parts[0].strip(),
            'title': parts[1].strip()
        }
    
    # 无法解析，使用文件名作为标题
    return {
        'artist': 'Unknown',
        'title': name
    }


def get_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    使用 mutagen 获取音频文件元数据
    
    如果 mutagen 不可用，则从文件名解析
    """
    metadata = {
        'title': None,
        'artist': None,
        'album': None,
        'album_artist': None,
        'genre': None,
        'year': None,
        'track_number': None,
        'disc_number': None,
        'duration_seconds': None,
        'bitrate_kbps': None,
        'sample_rate_hz': None,
        'channels': None
    }
    
    try:
        from mutagen import File as MutagenFile
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
        
        audio = MutagenFile(file_path)
        
        if audio is None:
            # 无法识别格式，从文件名解析
            parsed = parse_filename(os.path.basename(file_path))
            metadata['title'] = parsed['title']
            metadata['artist'] = parsed['artist']
            return metadata
        
        # 获取时长
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            metadata['duration_seconds'] = int(audio.info.length)
        
        # 获取比特率
        if hasattr(audio, 'info') and hasattr(audio.info, 'bitrate'):
            metadata['bitrate_kbps'] = int(audio.info.bitrate / 1000) if audio.info.bitrate else None
        
        # 获取采样率
        if hasattr(audio, 'info') and hasattr(audio.info, 'sample_rate'):
            metadata['sample_rate_hz'] = audio.info.sample_rate
        
        # 获取声道数
        if hasattr(audio, 'info') and hasattr(audio.info, 'channels'):
            metadata['channels'] = audio.info.channels
        
        # 获取标签
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            
            # MP3 (ID3)
            if hasattr(tags, 'get'):
                # 标题
                if 'TIT2' in tags:
                    metadata['title'] = str(tags['TIT2'])
                elif 'title' in tags:
                    metadata['title'] = str(tags['title'][0]) if tags['title'] else None
                
                # 艺术家
                if 'TPE1' in tags:
                    metadata['artist'] = str(tags['TPE1'])
                elif 'artist' in tags:
                    metadata['artist'] = str(tags['artist'][0]) if tags['artist'] else None
                
                # 专辑
                if 'TALB' in tags:
                    metadata['album'] = str(tags['TALB'])
                elif 'album' in tags:
                    metadata['album'] = str(tags['album'][0]) if tags['album'] else None
                
                # 专辑艺术家
                if 'TPE2' in tags:
                    metadata['album_artist'] = str(tags['TPE2'])
                elif 'albumartist' in tags:
                    metadata['album_artist'] = str(tags['albumartist'][0]) if tags['albumartist'] else None
                
                # 流派
                if 'TCON' in tags:
                    metadata['genre'] = str(tags['TCON'])
                elif 'genre' in tags:
                    metadata['genre'] = str(tags['genre'][0]) if tags['genre'] else None
                
                # 年份
                if 'TDRC' in tags:
                    try:
                        metadata['year'] = int(str(tags['TDRC'])[:4])
                    except:
                        pass
                elif 'date' in tags:
                    try:
                        metadata['year'] = int(str(tags['date'][0])[:4])
                    except:
                        pass
                
                # 轨道号
                if 'TRCK' in tags:
                    try:
                        track_str = str(tags['TRCK'])
                        metadata['track_number'] = int(track_str.split('/')[0])
                    except:
                        pass
                elif 'tracknumber' in tags:
                    try:
                        track_str = str(tags['tracknumber'][0])
                        metadata['track_number'] = int(track_str.split('/')[0])
                    except:
                        pass
                
                # 碟号
                if 'TPOS' in tags:
                    try:
                        disc_str = str(tags['TPOS'])
                        metadata['disc_number'] = int(disc_str.split('/')[0])
                    except:
                        pass
                elif 'discnumber' in tags:
                    try:
                        disc_str = str(tags['discnumber'][0])
                        metadata['disc_number'] = int(disc_str.split('/')[0])
                    except:
                        pass
        
        # 如果没有获取到标题或艺术家，从文件名解析
        if not metadata['title'] or not metadata['artist']:
            parsed = parse_filename(os.path.basename(file_path))
            if not metadata['title']:
                metadata['title'] = parsed['title']
            if not metadata['artist']:
                metadata['artist'] = parsed['artist']
        
        return metadata
        
    except ImportError:
        logger.warning("mutagen 未安装，将从文件名解析元数据")
        parsed = parse_filename(os.path.basename(file_path))
        metadata['title'] = parsed['title']
        metadata['artist'] = parsed['artist']
        return metadata
    except Exception as e:
        logger.warning(f"解析音频元数据失败 {file_path}: {e}")
        parsed = parse_filename(os.path.basename(file_path))
        metadata['title'] = parsed['title']
        metadata['artist'] = parsed['artist']
        return metadata


async def import_music_from_path(
    root_path: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    从指定路径导入音乐文件
    
    Args:
        root_path: 扫描的根目录
        dry_run: 如果为 True，只统计不写入数据库
    
    Returns:
        导入统计结果
    """
    from app.core.database import async_session_maker
    from app.models.music import Music, MusicFile
    from sqlalchemy import select
    
    stats = {
        'scanned_files': 0,
        'new_artists': 0,
        'new_albums': 0,
        'new_tracks': 0,
        'new_files': 0,
        'skipped_existing': 0,
        'skipped_unsupported': 0,
        'failed': 0,
        'errors': []
    }
    
    root = Path(root_path)
    if not root.exists():
        raise ValueError(f"路径不存在: {root_path}")
    
    if not root.is_dir():
        raise ValueError(f"路径不是目录: {root_path}")
    
    # 收集所有音频文件
    audio_files: List[Path] = []
    for ext in SUPPORTED_FORMATS:
        audio_files.extend(root.rglob(f"*{ext}"))
        audio_files.extend(root.rglob(f"*{ext.upper()}"))
    
    # 去重
    audio_files = list(set(audio_files))
    stats['scanned_files'] = len(audio_files)
    
    logger.info(f"扫描到 {len(audio_files)} 个音频文件")
    
    if dry_run:
        # 只统计，不写入
        for file_path in audio_files:
            try:
                metadata = get_audio_metadata(str(file_path))
                if metadata['title'] and metadata['artist']:
                    stats['new_tracks'] += 1
                    stats['new_files'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{file_path}: {str(e)}")
        
        return stats
    
    # 实际导入
    async with async_session_maker() as session:
        seen_artists = set()
        seen_albums = set()
        
        for file_path in audio_files:
            try:
                file_path_str = str(file_path)
                
                # 检查文件是否已存在
                existing = await session.execute(
                    select(MusicFile).where(MusicFile.file_path == file_path_str)
                )
                if existing.scalar_one_or_none():
                    stats['skipped_existing'] += 1
                    continue
                
                # 获取元数据
                metadata = get_audio_metadata(file_path_str)
                
                if not metadata['title'] or not metadata['artist']:
                    stats['failed'] += 1
                    stats['errors'].append(f"{file_path}: 无法解析标题或艺术家")
                    continue
                
                # 统计新艺术家
                if metadata['artist'] not in seen_artists:
                    seen_artists.add(metadata['artist'])
                    stats['new_artists'] += 1
                
                # 统计新专辑
                album_key = (metadata['artist'], metadata['album'])
                if album_key not in seen_albums and metadata['album']:
                    seen_albums.add(album_key)
                    stats['new_albums'] += 1
                
                # 创建 Music 记录
                music = Music(
                    title=metadata['title'],
                    artist=metadata['artist'],
                    album=metadata['album'],
                    album_artist=metadata['album_artist'],
                    genre=metadata['genre'],
                    year=metadata['year']
                )
                session.add(music)
                await session.flush()  # 获取 ID
                
                # 创建 MusicFile 记录
                file_stat = file_path.stat()
                file_size_bytes = file_stat.st_size
                
                music_file = MusicFile(
                    music_id=music.id,
                    file_path=file_path_str,
                    file_size_bytes=file_size_bytes,
                    format=file_path.suffix.lstrip('.').lower(),
                    duration_seconds=metadata['duration_seconds'],
                    bitrate_kbps=metadata['bitrate_kbps'],
                    sample_rate_hz=metadata['sample_rate_hz'],
                    channels=metadata['channels'],
                    track_number=metadata['track_number'],
                    disc_number=metadata['disc_number']
                )
                session.add(music_file)
                
                stats['new_tracks'] += 1
                stats['new_files'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{file_path}: {str(e)}")
                logger.error(f"导入失败 {file_path}: {e}")
        
        await session.commit()
    
    return stats


async def main():
    parser = argparse.ArgumentParser(description='音乐导入工具')
    parser.add_argument('--root', required=True, help='扫描的根目录')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际写入')
    
    args = parser.parse_args()
    
    logger.info(f"开始扫描目录: {args.root}")
    logger.info(f"模式: {'预览' if args.dry_run else '实际导入'}")
    
    try:
        stats = await import_music_from_path(args.root, dry_run=args.dry_run)
        
        print("\n========== 导入统计 ==========")
        print(f"扫描文件数: {stats['scanned_files']}")
        print(f"新增艺术家: {stats['new_artists']}")
        print(f"新增专辑: {stats['new_albums']}")
        print(f"新增曲目: {stats['new_tracks']}")
        print(f"新增文件: {stats['new_files']}")
        print(f"跳过已存在: {stats['skipped_existing']}")
        print(f"失败: {stats['failed']}")
        
        if stats['errors']:
            print("\n错误详情:")
            for error in stats['errors'][:10]:  # 只显示前 10 个错误
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... 还有 {len(stats['errors']) - 10} 个错误")
        
        print("==============================\n")
        
    except Exception as e:
        logger.error(f"导入失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
