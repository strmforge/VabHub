"""
音乐元数据提取器
从音频文件中提取元数据（标题、艺术家、专辑、封面等）
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any
from loguru import logger

try:
    import mutagen
    from mutagen.id3 import ID3NoHeaderError
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    from mutagen.easyid3 import EasyID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen库未安装，无法提取音乐元数据。请运行: pip install mutagen")


class MusicMetadataExtractor:
    """音乐元数据提取器"""
    
    def __init__(self):
        self.supported_formats = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取音乐文件元数据"""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen库未安装，返回基本元数据")
            return self._extract_basic_metadata(file_path)
        
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                return self._extract_basic_metadata(file_path)
            
            metadata = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'format': self._get_audio_format(file_path),
            }
            
            # 提取音频信息
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                metadata.update({
                    'duration': int(info.length) if info.length else None,
                    'bitrate': info.bitrate if hasattr(info, 'bitrate') else None,
                    'sample_rate': info.sample_rate if hasattr(info, 'sample_rate') else None,
                    'channels': info.channels if hasattr(info, 'channels') else None,
                })
            
            # 提取标签信息
            tags = self._extract_tags(audio_file)
            metadata.update(tags)
            
            # 提取专辑封面
            cover_data = self._extract_cover_art(audio_file)
            if cover_data:
                metadata['cover_art'] = cover_data
            
            return metadata
            
        except Exception as e:
            logger.error(f"提取音乐元数据失败 {file_path}: {e}")
            return self._extract_basic_metadata(file_path)
    
    def _extract_tags(self, audio_file) -> Dict[str, Any]:
        """提取音频标签"""
        tags = {}
        
        try:
            # 通用标签映射
            tag_mapping = {
                'title': ['TIT2', 'TITLE', '\xa9nam', 'title'],
                'artist': ['TPE1', 'ARTIST', '\xa9ART', 'artist'],
                'album': ['TALB', 'ALBUM', '\xa9alb', 'album'],
                'albumartist': ['TPE2', 'ALBUMARTIST', 'aART', 'albumartist'],
                'date': ['TDRC', 'DATE', '\xa9day', 'date'],
                'year': ['TYER', 'YEAR', '\xa9day', 'date'],
                'genre': ['TCON', 'GENRE', '\xa9gen', 'genre'],
                'track': ['TRCK', 'TRACKNUMBER', 'trkn', 'tracknumber'],
                'disc': ['TPOS', 'DISCNUMBER', 'disk', 'discnumber'],
                'composer': ['TCOM', 'COMPOSER', '\xa9wrt', 'composer'],
                'comment': ['COMM', 'COMMENT', '\xa9cmt', 'comment'],
            }
            
            for tag_name, possible_keys in tag_mapping.items():
                value = None
                
                # 尝试不同的标签格式
                for key in possible_keys:
                    try:
                        if isinstance(audio_file, EasyID3):
                            # MP3 EasyID3格式
                            if key in audio_file:
                                raw_value = audio_file[key]
                                if isinstance(raw_value, list) and raw_value:
                                    value = str(raw_value[0])
                                else:
                                    value = str(raw_value)
                                break
                        elif isinstance(audio_file, (FLAC, OggVorbis)):
                            # FLAC/OGG格式
                            if audio_file.tags and key in audio_file.tags:
                                raw_value = audio_file.tags[key]
                                if isinstance(raw_value, list) and raw_value:
                                    value = str(raw_value[0])
                                else:
                                    value = str(raw_value)
                                break
                        elif isinstance(audio_file, MP4):
                            # MP4/M4A格式
                            if key in audio_file:
                                raw_value = audio_file[key]
                                if isinstance(raw_value, list) and raw_value:
                                    value = str(raw_value[0])
                                else:
                                    value = str(raw_value)
                                break
                    except (KeyError, AttributeError):
                        continue
                
                if value:
                    # 特殊处理
                    if tag_name in ['track', 'disc'] and '/' in value:
                        value = value.split('/')[0]
                    elif tag_name in ['year', 'date'] and len(value) >= 4:
                        value = value[:4]
                    
                    tags[tag_name] = value
            
            # 设置默认值
            tags.setdefault('title', 'Unknown Title')
            tags.setdefault('artist', 'Unknown Artist')
            tags.setdefault('album', 'Unknown Album')
            tags.setdefault('genre', 'Unknown')
            
        except Exception as e:
            logger.warning(f"提取音频标签失败: {e}")
        
        return tags
    
    def _extract_cover_art(self, audio_file) -> Optional[Dict[str, Any]]:
        """提取专辑封面"""
        try:
            cover_data = None
            
            if isinstance(audio_file, MP3):
                # MP3文件：从ID3标签提取APIC
                try:
                    from mutagen.id3 import ID3, APIC
                    id3 = ID3(audio_file.filename)
                    if 'APIC:' in id3:
                        apic = id3['APIC:'].data
                        cover_data = {
                            'data': apic,
                            'mime_type': id3['APIC:'].mime,
                            'description': id3['APIC:'].desc or 'Cover'
                        }
                except (ID3NoHeaderError, KeyError, AttributeError):
                    pass
            
            elif isinstance(audio_file, FLAC):
                # FLAC文件：从PICTURE标签提取
                if audio_file.pictures:
                    picture = audio_file.pictures[0]
                    cover_data = {
                        'data': picture.data,
                        'mime_type': picture.mime,
                        'description': picture.desc or 'Cover'
                    }
            
            elif isinstance(audio_file, MP4):
                # MP4/M4A文件：从covr标签提取
                if 'covr' in audio_file:
                    covr = audio_file['covr'][0]
                    cover_data = {
                        'data': bytes(covr),
                        'mime_type': 'image/jpeg',  # MP4通常使用JPEG
                        'description': 'Cover'
                    }
            
            return cover_data
            
        except Exception as e:
            logger.warning(f"提取专辑封面失败: {e}")
            return None
    
    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取基本元数据（当mutagen不可用时）"""
        try:
            file_stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            
            # 尝试从文件名解析信息
            name_without_ext = os.path.splitext(file_name)[0]
            parts = name_without_ext.split(' - ')
            
            artist = parts[0] if len(parts) > 1 else "Unknown Artist"
            title = parts[1] if len(parts) > 1 else name_without_ext
            
            return {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_stat.st_size,
                'format': self._get_audio_format(file_path),
                'title': title,
                'artist': artist,
                'album': "Unknown Album",
                'duration': 0,
                'bitrate': 0,
            }
            
        except Exception as e:
            logger.error(f"提取基本元数据失败 {file_path}: {e}")
            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': 0,
                'format': 'Unknown',
                'title': 'Unknown Title',
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
            }
    
    def _get_audio_format(self, file_path: str) -> str:
        """获取音频格式"""
        ext = os.path.splitext(file_path)[1].lower()
        format_mapping = {
            '.mp3': 'MP3',
            '.flac': 'FLAC',
            '.wav': 'WAV',
            '.aac': 'AAC',
            '.ogg': 'OGG',
            '.m4a': 'M4A',
            '.wma': 'WMA'
        }
        return format_mapping.get(ext, 'Unknown')
    
    def save_cover_art(self, cover_data: Dict[str, Any], output_path: str) -> bool:
        """保存专辑封面到文件"""
        try:
            if not cover_data or 'data' not in cover_data:
                return False
            
            # 确定文件扩展名
            mime_type = cover_data.get('mime_type', 'image/jpeg')
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            ext = ext_map.get(mime_type, '.jpg')
            
            # 确保输出路径有正确的扩展名
            output_path = os.path.splitext(output_path)[0] + ext
            
            # 保存封面
            with open(output_path, 'wb') as f:
                f.write(cover_data['data'])
            
            logger.info(f"专辑封面已保存: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存专辑封面失败: {e}")
            return False

