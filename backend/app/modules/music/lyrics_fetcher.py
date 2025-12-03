"""
歌词获取器
从多个来源获取音乐歌词
"""

import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from app.core.cache import get_cache


class LyricsFetcher:
    """歌词获取器"""
    
    def __init__(self):
        self.cache = get_cache()
        # 歌词API服务
        self.lyrics_apis = {
            'netease': 'https://netease-cloud-music-api-psi-six.vercel.app',
            'qq_music': 'https://c.y.qq.com',
            'lyrics_ovh': 'https://api.lyrics.ovh/v1',  # 免费歌词API
        }
    
    async def fetch_lyrics(
        self,
        title: str,
        artist: str,
        platform: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取歌词"""
        if not title or not artist:
            return None
        
        # 检查缓存
        cache_key = f"lyrics_{artist}_{title}"
        cached_lyrics = await self.cache.get(cache_key)
        if cached_lyrics:
            logger.debug(f"从缓存获取歌词: {artist} - {title}")
            return cached_lyrics
        
        lyrics_data = None
        
        # 按优先级尝试不同来源
        if platform == 'netease' or platform is None:
            lyrics_data = await self._fetch_from_netease(title, artist)
        
        if not lyrics_data and (platform == 'qq_music' or platform is None):
            lyrics_data = await self._fetch_from_qq_music(title, artist)
        
        if not lyrics_data:
            lyrics_data = await self._fetch_from_lyrics_ovh(title, artist)
        
        # 保存到缓存（7天）
        if lyrics_data:
            await self.cache.set(cache_key, lyrics_data, ttl=604800)
        
        return lyrics_data
    
    async def _fetch_from_netease(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """从网易云音乐获取歌词"""
        try:
            # 先搜索歌曲
            search_url = f"{self.lyrics_apis['netease']}/search"
            async with httpx.AsyncClient(timeout=10.0) as client:
                search_response = await client.get(search_url, params={
                    'keywords': f"{artist} {title}",
                    'type': 1,  # 1=歌曲
                    'limit': 1
                })
                
                if search_response.status_code != 200:
                    return None
                
                search_data = search_response.json()
                songs = search_data.get('result', {}).get('songs', [])
                if not songs:
                    return None
                
                song_id = songs[0].get('id')
                if not song_id:
                    return None
                
                # 获取歌词
                lyrics_url = f"{self.lyrics_apis['netease']}/lyric"
                lyrics_response = await client.get(lyrics_url, params={'id': song_id})
                
                if lyrics_response.status_code != 200:
                    return None
                
                lyrics_data = lyrics_response.json()
                lrc = lyrics_data.get('lrc', {}).get('lyric', '')
                tlyric = lyrics_data.get('tlyric', {}).get('lyric', '')  # 翻译歌词
                
                if lrc:
                    return {
                        'lyrics': lrc,
                        'translation': tlyric if tlyric else None,
                        'source': 'netease',
                        'platform_id': str(song_id)
                    }
        
        except Exception as e:
            logger.warning(f"从网易云音乐获取歌词失败: {e}")
        
        return None
    
    async def _fetch_from_qq_music(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """从QQ音乐获取歌词"""
        try:
            # QQ音乐需要先搜索歌曲获取songmid
            search_url = f"{self.lyrics_apis['qq_music']}/soso/fcgi-bin/client_search_cp"
            async with httpx.AsyncClient(timeout=10.0) as client:
                search_response = await client.get(search_url, params={
                    'ct': 24,
                    'qqmusic_ver': 1298,
                    'new_json': 1,
                    'remoteplace': 'txt.yqq.song',
                    'searchid': '',
                    't': 0,
                    'aggr': 1,
                    'cr': 1,
                    'catZhida': 1,
                    'lossless': 0,
                    'flag_qc': 0,
                    'p': 1,
                    'n': 1,
                    'w': f"{artist} {title}",
                    'g_tk': 5381,
                    'loginUin': 0,
                    'hostUin': 0,
                    'format': 'json',
                    'inCharset': 'utf8',
                    'outCharset': 'utf-8',
                    'notice': 0,
                    'platform': 'yqq.json',
                    'needNewCode': 0
                })
                
                if search_response.status_code != 200:
                    return None
                
                # 解析JSONP响应
                text = search_response.text
                if text.startswith('callback(') and text.endswith(')'):
                    text = text[9:-1]
                
                import json
                search_data = json.loads(text)
                songs = search_data.get('data', {}).get('song', {}).get('list', [])
                if not songs:
                    return None
                
                songmid = songs[0].get('songmid')
                if not songmid:
                    return None
                
                # 获取歌词
                lyrics_url = f"{self.lyrics_apis['qq_music']}/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
                lyrics_response = await client.get(lyrics_url, params={
                    'songmid': songmid,
                    'format': 'json',
                    'nobase64': 1,
                    'musicid': songs[0].get('songid', ''),
                    'g_tk': 5381,
                    'loginUin': 0,
                    'hostUin': 0,
                    'format': 'json',
                    'inCharset': 'utf8',
                    'outCharset': 'utf-8',
                    'notice': 0,
                    'platform': 'yqq.json',
                    'needNewCode': 0
                })
                
                if lyrics_response.status_code != 200:
                    return None
                
                lyrics_text = lyrics_response.text
                if lyrics_text.startswith('callback(') and lyrics_text.endswith(')'):
                    lyrics_text = lyrics_text[9:-1]
                
                lyrics_data = json.loads(lyrics_text)
                lyric = lyrics_data.get('lyric', '')
                
                if lyric:
                    return {
                        'lyrics': lyric,
                        'translation': None,
                        'source': 'qq_music',
                        'platform_id': songmid
                    }
        
        except Exception as e:
            logger.warning(f"从QQ音乐获取歌词失败: {e}")
        
        return None
    
    async def _fetch_from_lyrics_ovh(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """从Lyrics.ovh获取歌词（免费API）"""
        try:
            url = f"{self.lyrics_apis['lyrics_ovh']}/{artist}/{title}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    lyrics = data.get('lyrics', '')
                    
                    if lyrics:
                        return {
                            'lyrics': lyrics,
                            'translation': None,
                            'source': 'lyrics_ovh'
                        }
        
        except Exception as e:
            logger.warning(f"从Lyrics.ovh获取歌词失败: {e}")
        
        return None
    
    def parse_lyrics_with_timestamps(self, lyrics_text: str) -> List[Dict[str, Any]]:
        """解析带时间戳的歌词（LRC格式）"""
        lines = []
        
        try:
            import re
            # LRC格式：[mm:ss.xx]歌词内容
            pattern = r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)'
            
            for line in lyrics_text.split('\n'):
                match = re.match(pattern, line)
                if match:
                    minutes, seconds, centiseconds, text = match.groups()
                    timestamp = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
                    lines.append({
                        'time': timestamp,
                        'text': text.strip()
                    })
                elif line.strip():
                    # 没有时间戳的歌词行
                    lines.append({
                        'time': None,
                        'text': line.strip()
                    })
        
        except Exception as e:
            logger.warning(f"解析歌词时间戳失败: {e}")
        
        return lines

