"""
网易云音乐平台客户端
集成网易云音乐API提供音乐搜索、推荐等功能
"""
import aiohttp
import json
from typing import Dict, List, Optional, Any
from loguru import logger


class NeteaseClient:
    """网易云音乐客户端"""
    
    def __init__(self):
        self.base_url = "https://music.163.com"
        self.api_url = "https://music.163.com/weapi"
        # 使用第三方公开API作为备选
        self.public_api_url = "https://netease-cloud-music-api-psi-six.vercel.app"
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    async def _make_public_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用公开API发起请求"""
        try:
            # 映射端点
            endpoint_mapping = {
                'search/get': 'search',
                'toplist': 'toplist',
                'playlist/detail': 'playlist/detail',
                'song/detail': 'song/detail',
                'artist/songs': 'artists',
                'album': 'album'
            }
            
            mapped_endpoint = endpoint_mapping.get(endpoint, endpoint)
            url = f"{self.public_api_url}/{mapped_endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 第三方API返回格式：{"code": 200, "result": {...}}
                        if data.get('code') == 200:
                            return data
                        return data
                    else:
                        logger.warning(f"网易云音乐公开API请求失败: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"网易云音乐公开API请求失败: {e}")
            return {}
    
    async def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索音乐"""
        try:
            # 映射搜索类型
            type_mapping = {
                "all": 1018,    # 综合
                "track": 1,     # 单曲
                "album": 10,    # 专辑
                "artist": 100,  # 歌手
                "song": 1,
                "playlist": 1000
            }
            
            netease_type = type_mapping.get(search_type, 1)
            
            params = {
                'keywords': query,
                'type': netease_type,
                'limit': min(limit, 100),
                'offset': 0
            }
            
            response = await self._make_public_request("search/get", params)
            
            if response.get('code') != 200:
                logger.warning(f"网易云音乐搜索返回错误: {response.get('code')}")
                return []
            
            results = []
            result_data = response.get('result', {})
            
            # 处理单曲搜索结果
            if 'songs' in result_data:
                for song in result_data['songs']:
                    track_data = self._format_track(song)
                    if track_data:
                        results.append(track_data)
            
            # 处理专辑搜索结果
            if 'albums' in result_data:
                for album in result_data['albums']:
                    album_data = self._format_album(album)
                    if album_data:
                        results.append(album_data)
            
            # 处理歌手搜索结果
            if 'artists' in result_data:
                for artist in result_data['artists']:
                    artist_data = self._format_artist(artist)
                    if artist_data:
                        results.append(artist_data)
            
            # 处理播放列表搜索结果
            if 'playlists' in result_data:
                for playlist in result_data['playlists']:
                    playlist_data = self._format_playlist(playlist)
                    if playlist_data:
                        results.append(playlist_data)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"网易云音乐搜索失败: {e}")
            return []
    
    def _format_track(self, song: Dict[str, Any]) -> Dict[str, Any]:
        """格式化曲目数据"""
        try:
            # 获取歌手名称
            artists = song.get('artists', []) or song.get('ar', [])
            artist_names = []
            for artist in artists:
                if isinstance(artist, dict):
                    artist_names.append(artist.get('name', ''))
                elif isinstance(artist, str):
                    artist_names.append(artist)
            
            artist = ', '.join([name for name in artist_names if name]) or '未知歌手'
            
            # 获取专辑信息
            album_info = song.get('album', {}) or song.get('al', {})
            album_name = album_info.get('name', '未知专辑') if isinstance(album_info, dict) else '未知专辑'
            
            # 构建封面图片URL
            pic_url = None
            if isinstance(album_info, dict):
                pic_url = album_info.get('picUrl') or album_info.get('blurPicUrl') or album_info.get('pic')
            
            return {
                'id': str(song.get('id', '')),
                'type': 'track',
                'platform': 'netease',
                'title': song.get('name', ''),
                'artist': artist,
                'album': album_name,
                'duration': (song.get('duration', 0) or song.get('dt', 0)) // 1000,  # 转换为秒
                'popularity': song.get('popularity', 0) or song.get('pop', 0),
                'preview_url': None,  # 网易云音乐需要特殊处理播放链接
                'external_url': f"https://music.163.com/#/song?id={song.get('id', '')}",
                'cover_url': pic_url,
                'release_date': None,
                'explicit': song.get('fee', 0) != 0,  # 付费歌曲标记
                'mvid': song.get('mvid', 0)
            }
        except Exception as e:
            logger.warning(f"格式化网易云音乐曲目数据失败: {e}")
            return {}
    
    def _format_album(self, album: Dict[str, Any]) -> Dict[str, Any]:
        """格式化专辑数据"""
        try:
            # 获取歌手名称
            artist_info = album.get('artist', {}) or album.get('ar', {}) or {}
            if isinstance(artist_info, list) and len(artist_info) > 0:
                artist_info = artist_info[0]
            
            artist_name = '未知歌手'
            if isinstance(artist_info, dict):
                artist_name = artist_info.get('name', '未知歌手')
            
            pic_url = album.get('picUrl') or album.get('blurPicUrl') or album.get('pic')
            
            return {
                'id': str(album.get('id', '')),
                'type': 'album',
                'platform': 'netease',
                'title': album.get('name', ''),
                'artist': artist_name,
                'album': album.get('name', ''),
                'total_tracks': album.get('size', 0),
                'popularity': 0,
                'external_url': f"https://music.163.com/#/album?id={album.get('id', '')}",
                'cover_url': pic_url,
                'release_date': album.get('publishTime'),
                'album_type': 'album'
            }
        except Exception as e:
            logger.warning(f"格式化网易云音乐专辑数据失败: {e}")
            return {}
    
    def _format_artist(self, artist: Dict[str, Any]) -> Dict[str, Any]:
        """格式化艺术家数据"""
        try:
            pic_url = artist.get('picUrl') or artist.get('img1v1Url') or artist.get('pic')
            
            return {
                'id': str(artist.get('id', '')),
                'type': 'artist',
                'platform': 'netease',
                'title': artist.get('name', ''),
                'artist': artist.get('name', ''),
                'popularity': 0,
                'followers': artist.get('fansCount', 0) or artist.get('musicSize', 0),
                'genres': [],
                'external_url': f"https://music.163.com/#/artist?id={artist.get('id', '')}",
                'cover_url': pic_url,
                'album_count': artist.get('albumSize', 0),
                'music_count': artist.get('musicSize', 0)
            }
        except Exception as e:
            logger.warning(f"格式化网易云音乐艺术家数据失败: {e}")
            return {}
    
    def _format_playlist(self, playlist: Dict[str, Any]) -> Dict[str, Any]:
        """格式化播放列表数据"""
        try:
            pic_url = playlist.get('coverImgUrl') or playlist.get('picUrl') or playlist.get('pic')
            
            return {
                'id': str(playlist.get('id', '')),
                'type': 'playlist',
                'platform': 'netease',
                'title': playlist.get('name', ''),
                'artist': playlist.get('creator', {}).get('nickname', '') if playlist.get('creator') else '',
                'total_tracks': playlist.get('trackCount', 0),
                'external_url': f"https://music.163.com/#/playlist?id={playlist.get('id', '')}",
                'cover_url': pic_url,
                'description': playlist.get('description'),
                'play_count': playlist.get('playCount', 0)
            }
        except Exception as e:
            logger.warning(f"格式化网易云音乐播放列表数据失败: {e}")
            return {}
    
    async def get_trending(self, region: str = "CN", limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门音乐（排行榜）"""
        try:
            # 获取热歌榜 (id: 3778678)
            params = {
                'id': 3778678,  # 网易云热歌榜ID
                'n': min(limit, 100)
            }
            
            response = await self._make_public_request("playlist/detail", params)
            
            if response.get('code') != 200:
                return []
            
            results = []
            playlist = response.get('playlist', {})
            tracks = playlist.get('tracks', [])
            
            for i, track in enumerate(tracks[:limit]):
                track_data = self._format_track(track)
                if track_data:
                    track_data['rank'] = i + 1
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取网易云音乐热门音乐失败: {e}")
            return []
    
    async def get_charts(self, chart_type: str = "hot", region: str = "CN", limit: int = 50) -> List[Dict[str, Any]]:
        """获取音乐榜单"""
        try:
            # 不同的榜单ID
            chart_ids = {
                "hot": 3778678,      # 热歌榜
                "new": 3779629,      # 新歌榜
                "trending": 19723756, # 飙升榜
                "original": 2884035   # 原创榜
            }
            
            chart_id = chart_ids.get(chart_type, chart_ids["hot"])
            
            params = {
                'id': chart_id,
                'n': min(limit, 100)
            }
            
            response = await self._make_public_request("playlist/detail", params)
            
            if response.get('code') != 200:
                return []
            
            results = []
            playlist = response.get('playlist', {})
            tracks = playlist.get('tracks', [])
            
            for i, track in enumerate(tracks[:limit]):
                track_data = self._format_track(track)
                if track_data:
                    track_data['rank'] = i + 1
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取网易云音乐榜单失败: {e}")
            return []
    
    async def get_artist(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """获取艺术家信息"""
        try:
            params = {
                'id': artist_id
            }
            
            response = await self._make_public_request("artist/songs", params)
            
            if response.get('code') != 200:
                return None
            
            artist_info = response.get('artist', {})
            
            if not artist_info:
                return None
            
            return self._format_artist(artist_info)
            
        except Exception as e:
            logger.error(f"获取网易云音乐艺术家信息失败: {e}")
            return None
    
    async def get_album(self, album_id: str) -> Optional[Dict[str, Any]]:
        """获取专辑信息"""
        try:
            params = {
                'id': album_id
            }
            
            response = await self._make_public_request("album", params)
            
            if response.get('code') != 200:
                return None
            
            album_info = response.get('album', {})
            
            if not album_info:
                return None
            
            # 格式化专辑信息
            album_data = self._format_album(album_info)
            
            # 获取专辑曲目
            tracks = []
            for song in album_info.get('songs', []):
                track_data = {
                    'id': song.get('id', ''),
                    'name': song.get('name', ''),
                    'track_number': song.get('no', 0),
                    'duration': song.get('duration', 0),
                    'preview_url': None,
                    'explicit': song.get('fee', 0) != 0
                }
                tracks.append(track_data)
            
            album_data['tracks'] = tracks
            album_data['total_tracks'] = len(tracks)
            
            return album_data
            
        except Exception as e:
            logger.error(f"获取网易云音乐专辑信息失败: {e}")
            return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """获取播放列表信息"""
        try:
            params = {
                'id': playlist_id
            }
            
            response = await self._make_public_request("playlist/detail", params)
            
            if response.get('code') != 200:
                return None
            
            playlist = response.get('playlist', {})
            
            if not playlist:
                return None
            
            return self._format_playlist(playlist)
            
        except Exception as e:
            logger.error(f"获取网易云音乐播放列表信息失败: {e}")
            return None

