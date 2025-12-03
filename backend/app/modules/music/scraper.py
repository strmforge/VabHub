"""
音乐刮削器
集成MusicBrainz和AcoustID音频指纹识别
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

try:
    import musicbrainzngs
    MUSICBRAINZ_AVAILABLE = True
except ImportError:
    MUSICBRAINZ_AVAILABLE = False
    logger.warning("musicbrainzngs库未安装，无法使用MusicBrainz功能。请运行: pip install musicbrainzngs")

try:
    import acoustid
    ACOUSTID_AVAILABLE = True
except ImportError:
    ACOUSTID_AVAILABLE = False
    logger.warning("pyacoustid库未安装，无法使用AcoustID功能。请运行: pip install pyacoustid")

from app.modules.music.metadata_extractor import MusicMetadataExtractor
from app.core.cache import get_cache


class MusicScraper:
    """音乐刮削器 - 集成MusicBrainz和AcoustID"""
    
    def __init__(self, acoustid_api_key: Optional[str] = None):
        """初始化音乐刮削器"""
        if MUSICBRAINZ_AVAILABLE:
            musicbrainzngs.set_useragent(
                "VabHub/1.0.0",
                "1.0.0",
                "contact@vabhub.com"
            )
        
        self.acoustid_api_key = acoustid_api_key
        self.metadata_extractor = MusicMetadataExtractor()
        self.cache = get_cache()
    
    async def scrape_music_file(self, file_path: str) -> Dict[str, Any]:
        """刮削音乐文件元数据"""
        # 检查缓存
        cache_key = f"music_scrape_{Path(file_path).name}_{os.path.getmtime(file_path)}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"从缓存获取刮削结果: {file_path}")
            return cached_result
        
        metadata = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'sources': [],
        }
        
        # 1. 从文件本身提取元数据
        file_metadata = self.metadata_extractor.extract_metadata(file_path)
        metadata.update(file_metadata)
        metadata['sources'].append('file_tags')
        
        # 2. 尝试音频指纹识别（优先级最高）
        fingerprint_result = None
        if ACOUSTID_AVAILABLE and self.acoustid_api_key:
            fingerprint = await self._generate_audio_fingerprint(file_path)
            if fingerprint:
                fingerprint_result = await self._lookup_by_fingerprint(fingerprint)
                if fingerprint_result:
                    metadata.update(fingerprint_result)
                    metadata['sources'].append('acoustid_fingerprint')
                    logger.info(f"音频指纹识别成功: {file_path}")
        
        # 3. 如果指纹识别失败，尝试MusicBrainz搜索
        if not fingerprint_result and MUSICBRAINZ_AVAILABLE:
            if file_metadata.get('title') or file_metadata.get('artist'):
                query_parts = []
                if file_metadata.get('artist'):
                    query_parts.append(file_metadata['artist'])
                if file_metadata.get('title'):
                    query_parts.append(file_metadata['title'])
                
                if query_parts:
                    query = ' '.join(query_parts)
                    mb_results = await self._search_musicbrainz(query, 'recording')
                    
                    if mb_results:
                        best_match = mb_results[0]
                        metadata.update(best_match)
                        metadata['sources'].append('musicbrainz_search')
                        logger.info(f"MusicBrainz搜索成功: {file_path}")
        
        # 4. 如果都没有结果，尝试基于文件名的搜索
        if not metadata.get('title') and not metadata.get('artist'):
            filename = Path(file_path).stem
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                metadata['artist'] = parts[0].strip()
                metadata['title'] = parts[1].strip()
                metadata['sources'].append('filename_parsing')
        
        # 保存到缓存（24小时）
        await self.cache.set(cache_key, metadata, ttl=86400)
        
        # 记录刮削结果
        success_sources = [s for s in metadata['sources'] if s != 'file_tags']
        if success_sources:
            logger.info(f"音乐文件刮削成功: {file_path} (来源: {', '.join(success_sources)})")
        else:
            logger.warning(f"音乐文件刮削失败: {file_path}")
        
        return metadata
    
    async def _generate_audio_fingerprint(self, file_path: str) -> Optional[str]:
        """生成音频指纹"""
        if not ACOUSTID_AVAILABLE:
            return None
        
        try:
            if not os.path.exists(file_path):
                return None
            
            # 文件大小限制
            file_size = os.path.getsize(file_path)
            if file_size > 500 * 1024 * 1024:  # 500MB
                logger.warning(f"文件过大，跳过指纹生成: {file_path}")
                return None
            
            # 在后台线程中生成指纹（避免阻塞）
            loop = asyncio.get_event_loop()
            duration, fingerprint = await loop.run_in_executor(
                None,
                acoustid.fingerprint_file,
                file_path
            )
            
            if len(fingerprint) < 50:
                logger.warning(f"音频指纹质量不佳: {file_path}")
                return None
            
            return fingerprint
            
        except Exception as e:
            logger.error(f"生成音频指纹失败 {file_path}: {e}")
            return None
    
    async def _lookup_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """通过音频指纹查找音乐"""
        if not self.acoustid_api_key or not ACOUSTID_AVAILABLE:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                acoustid.lookup,
                self.acoustid_api_key,
                fingerprint,
                'recordings releases'
            )
            
            if not results:
                return None
            
            # 按匹配分数排序
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            best_result = sorted_results[0]
            
            # 检查匹配分数阈值
            score = best_result.get('score', 0)
            if score < 0.7:
                logger.info(f"匹配分数过低: {score}")
                return None
            
            return self._parse_acoustid_result(best_result)
            
        except Exception as e:
            logger.error(f"AcoustID指纹查找失败: {e}")
            return None
    
    async def _search_musicbrainz(self, query: str, search_type: str = "recording") -> List[Dict[str, Any]]:
        """搜索MusicBrainz数据库"""
        if not MUSICBRAINZ_AVAILABLE:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            if search_type == "recording":
                result = await loop.run_in_executor(
                    None,
                    musicbrainzngs.search_recordings,
                    query,
                    5
                )
                recordings = result.get('recording-list', [])
                return [self._parse_musicbrainz_recording(rec) for rec in recordings]
            elif search_type == "release":
                result = await loop.run_in_executor(
                    None,
                    musicbrainzngs.search_releases,
                    query,
                    5
                )
                releases = result.get('release-list', [])
                return [self._parse_musicbrainz_release(rel) for rel in releases]
            elif search_type == "artist":
                result = await loop.run_in_executor(
                    None,
                    musicbrainzngs.search_artists,
                    query,
                    5
                )
                artists = result.get('artist-list', [])
                return [self._parse_musicbrainz_artist(art) for art in artists]
            
            return []
            
        except Exception as e:
            logger.error(f"MusicBrainz搜索失败: {e}")
            return []
    
    def _parse_musicbrainz_recording(self, recording: Dict[str, Any]) -> Dict[str, Any]:
        """解析MusicBrainz录音信息"""
        return {
            'title': recording.get('title'),
            'artist': recording.get('artist-credit-phrase'),
            'album': recording.get('release-list', [{}])[0].get('title') if recording.get('release-list') else None,
            'year': recording.get('release-list', [{}])[0].get('date') if recording.get('release-list') else None,
            'mbid': recording.get('id'),
            'duration': recording.get('length'),
            'source': 'musicbrainz'
        }
    
    def _parse_musicbrainz_release(self, release: Dict[str, Any]) -> Dict[str, Any]:
        """解析MusicBrainz发行信息"""
        return {
            'title': release.get('title'),
            'artist': release.get('artist-credit-phrase'),
            'year': release.get('date'),
            'country': release.get('country'),
            'mbid': release.get('id'),
            'type': release.get('release-group', {}).get('type'),
            'source': 'musicbrainz'
        }
    
    def _parse_musicbrainz_artist(self, artist: Dict[str, Any]) -> Dict[str, Any]:
        """解析MusicBrainz艺术家信息"""
        return {
            'name': artist.get('name'),
            'mbid': artist.get('id'),
            'type': artist.get('type'),
            'country': artist.get('country'),
            'source': 'musicbrainz'
        }
    
    def _parse_acoustid_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """解析AcoustID结果"""
        recordings = result.get('recordings', [])
        if not recordings:
            return {}
        
        recording = recordings[0]
        return {
            'title': recording.get('title'),
            'artist': recording.get('artists', [{}])[0].get('name') if recording.get('artists') else None,
            'album': recording.get('releasegroups', [{}])[0].get('title') if recording.get('releasegroups') else None,
            'mbid': recording.get('id'),
            'score': result.get('score'),
            'source': 'acoustid'
        }
    
    async def batch_scrape_music_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量刮削音乐文件"""
        results = {}
        
        # 并发处理（限制并发数）
        semaphore = asyncio.Semaphore(5)
        
        async def scrape_with_semaphore(file_path: str):
            async with semaphore:
                if os.path.exists(file_path):
                    return file_path, await self.scrape_music_file(file_path)
                else:
                    return file_path, {'error': '文件不存在'}
        
        tasks = [scrape_with_semaphore(fp) for fp in file_paths]
        scrape_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in scrape_results:
            if isinstance(result, Exception):
                logger.error(f"批量刮削失败: {result}")
                continue
            file_path, metadata = result
            results[file_path] = metadata
        
        return results

