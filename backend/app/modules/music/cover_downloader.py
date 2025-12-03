"""
专辑封面下载器
从多个来源下载专辑封面
"""

import httpx
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from app.core.cache import get_cache


class CoverDownloader:
    """专辑封面下载器"""
    
    def __init__(self):
        self.cache = get_cache()
        self.cover_cache_dir = Path("data/covers")
        self.cover_cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_cover(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        platform: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """下载专辑封面"""
        if not title or not artist:
            return None
        
        # 检查缓存
        cache_key = f"cover_{artist}_{album or title}"
        cached_cover = await self.cache.get(cache_key)
        if cached_cover and os.path.exists(cached_cover):
            logger.debug(f"从缓存获取封面: {artist} - {album or title}")
            return cached_cover
        
        cover_url = None
        
        # 按优先级尝试不同来源
        if platform == 'netease' or platform is None:
            cover_url = await self._get_cover_url_from_netease(title, artist, album)
        
        if not cover_url and (platform == 'qq_music' or platform is None):
            cover_url = await self._get_cover_url_from_qq_music(title, artist, album)
        
        if not cover_url:
            cover_url = await self._get_cover_url_from_lastfm(title, artist, album)
        
        if not cover_url:
            cover_url = await self._get_cover_url_from_musicbrainz(title, artist, album)
        
        # 下载封面
        if cover_url:
            saved_path = await self._download_image(cover_url, save_path)
            if saved_path:
                await self.cache.set(cache_key, saved_path, ttl=2592000)  # 30天
                return saved_path
        
        return None
    
    async def _get_cover_url_from_netease(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[str]:
        """从网易云音乐获取封面URL"""
        try:
            api_url = "https://netease-cloud-music-api-psi-six.vercel.app/search"
            async with httpx.AsyncClient(timeout=10.0) as client:
                query = f"{artist} {title}" if not album else f"{artist} {album}"
                response = await client.get(api_url, params={
                    'keywords': query,
                    'type': 1 if not album else 10,  # 1=歌曲, 10=专辑
                    'limit': 1
                })
                
                if response.status_code == 200:
                    data = response.json()
                    songs = data.get('result', {}).get('songs', [])
                    if songs:
                        album_info = songs[0].get('album', {})
                        pic_url = album_info.get('picUrl')
                        if pic_url:
                            return pic_url
        
        except Exception as e:
            logger.warning(f"从网易云音乐获取封面失败: {e}")
        
        return None
    
    async def _get_cover_url_from_qq_music(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[str]:
        """从QQ音乐获取封面URL"""
        try:
            search_url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url, params={
                    'w': f"{artist} {title}",
                    'format': 'json',
                    'inCharset': 'utf8',
                    'outCharset': 'utf-8',
                    'platform': 'yqq.json',
                    'needNewCode': 0
                })
                
                if response.status_code == 200:
                    text = response.text
                    if text.startswith('callback(') and text.endswith(')'):
                        text = text[9:-1]
                    
                    import json
                    data = json.loads(text)
                    songs = data.get('data', {}).get('song', {}).get('list', [])
                    if songs:
                        album_mid = songs[0].get('albummid')
                        if album_mid:
                            # QQ音乐封面URL格式
                            return f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{album_mid}.jpg"
        
        except Exception as e:
            logger.warning(f"从QQ音乐获取封面失败: {e}")
        
        return None
    
    async def _get_cover_url_from_lastfm(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[str]:
        """从Last.fm获取封面URL"""
        try:
            # Last.fm API需要API密钥，这里使用公开方法
            # 注意：实际使用时需要配置Last.fm API密钥
            api_key = os.getenv('LASTFM_API_KEY')
            if not api_key:
                return None
            
            api_url = "http://ws.audioscrobbler.com/2.0/"
            async with httpx.AsyncClient(timeout=10.0) as client:
                method = 'album.getinfo' if album else 'track.getInfo'
                params = {
                    'method': method,
                    'api_key': api_key,
                    'format': 'json',
                    'artist': artist,
                    'track': title if not album else None,
                    'album': album
                }
                
                response = await client.get(api_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if album:
                        images = data.get('album', {}).get('image', [])
                    else:
                        images = data.get('track', {}).get('album', {}).get('image', [])
                    
                    # 选择最大尺寸的封面
                    for img in reversed(images):  # 从大到小
                        if img.get('#text'):
                            return img['#text']
        
        except Exception as e:
            logger.warning(f"从Last.fm获取封面失败: {e}")
        
        return None
    
    async def _get_cover_url_from_musicbrainz(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[str]:
        """从MusicBrainz获取封面URL（通过Cover Art Archive）"""
        try:
            # 先搜索MusicBrainz获取release ID
            import musicbrainzngs
            musicbrainzngs.set_useragent("VabHub/1.0.0", "1.0.0", "contact@vabhub.com")
            
            query = f"{artist} {album or title}"
            result = musicbrainzngs.search_releases(query=query, limit=1)
            releases = result.get('release-list', [])
            
            if releases:
                release_id = releases[0].get('id')
                # Cover Art Archive URL
                return f"https://coverartarchive.org/release/{release_id}/front"
        
        except Exception as e:
            logger.warning(f"从MusicBrainz获取封面失败: {e}")
        
        return None
    
    async def _download_image(self, url: str, save_path: Optional[str] = None) -> Optional[str]:
        """下载图片"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code != 200:
                    return None
                
                # 确定保存路径
                if not save_path:
                    # 从URL提取文件名或使用哈希
                    import hashlib
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    ext = '.jpg'  # 默认JPEG
                    if '.png' in url.lower():
                        ext = '.png'
                    elif '.webp' in url.lower():
                        ext = '.webp'
                    save_path = str(self.cover_cache_dir / f"{url_hash}{ext}")
                
                # 确保目录存在
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # 保存图片
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"封面已下载: {save_path}")
                return save_path
        
        except Exception as e:
            logger.error(f"下载封面失败 {url}: {e}")
            return None
    
    async def extract_and_save_cover_from_file(
        self,
        file_path: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """从音乐文件中提取并保存封面"""
        try:
            from app.modules.music.metadata_extractor import MusicMetadataExtractor
            extractor = MusicMetadataExtractor()
            
            metadata = extractor.extract_metadata(file_path)
            cover_data = metadata.get('cover_art')
            
            if not cover_data:
                return None
            
            # 确定输出路径
            if not output_path:
                base_path = Path(file_path).parent
                file_name = Path(file_path).stem
                mime_type = cover_data.get('mime_type', 'image/jpeg')
                ext_map = {
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'image/webp': '.webp'
                }
                ext = ext_map.get(mime_type, '.jpg')
                output_path = str(base_path / f"{file_name}_cover{ext}")
            
            # 保存封面
            success = extractor.save_cover_art(cover_data, output_path)
            if success:
                return output_path
        
        except Exception as e:
            logger.error(f"从文件提取封面失败 {file_path}: {e}")
        
        return None

