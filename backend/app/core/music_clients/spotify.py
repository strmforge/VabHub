"""
Spotify 音乐平台客户端
集成 Spotify Web API 提供音乐搜索、推荐等功能
"""
import aiohttp
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


class SpotifyClient:
    """Spotify 客户端"""
    
    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://api.spotify.com/v1"
        self.auth_url = "https://accounts.spotify.com/api/token"
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        try:
            # 检查现有令牌是否有效
            if (self.access_token and self.token_expires_at and 
                datetime.now() < self.token_expires_at):
                return self.access_token
            
            if not self.client_id or not self.client_secret:
                raise ValueError("Spotify Client ID 和 Secret 未配置")
            
            # 获取新令牌
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.auth_url, headers=headers, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        expires_in = token_data.get('expires_in', 3600)
                        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                        return self.access_token
                    else:
                        error_text = await response.text()
                        raise Exception(f"获取 Spotify 访问令牌失败: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"获取 Spotify 访问令牌失败: {e}")
            raise
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发起 API 请求"""
        try:
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.warning(f"Spotify API 请求失败: {response.status} - {error_text}")
                        return {}
        
        except Exception as e:
            logger.error(f"Spotify API 请求失败: {e}")
            return {}
    
    async def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 20,
        market: str = "CN"
    ) -> List[Dict[str, Any]]:
        """搜索音乐"""
        try:
            # 映射搜索类型
            type_mapping = {
                "all": "track,album,artist",
                "track": "track",
                "album": "album",
                "artist": "artist",
                "song": "track",
                "playlist": "playlist"
            }
            
            spotify_type = type_mapping.get(search_type, "track")
            
            params = {
                'q': query,
                'type': spotify_type,
                'limit': min(limit, 50),  # Spotify 限制最大50
                'market': market
            }
            
            response = await self._make_request("search", params)
            
            if not response:
                return []
            
            results = []
            
            # 处理曲目搜索结果
            if 'tracks' in response and 'items' in response['tracks']:
                for track in response['tracks']['items']:
                    results.append(self._format_track(track))
            
            # 处理专辑搜索结果
            if 'albums' in response and 'items' in response['albums']:
                for album in response['albums']['items']:
                    results.append(self._format_album(album))
            
            # 处理艺术家搜索结果
            if 'artists' in response and 'items' in response['artists']:
                for artist in response['artists']['items']:
                    results.append(self._format_artist(artist))
            
            # 处理播放列表搜索结果
            if 'playlists' in response and 'items' in response['playlists']:
                for playlist in response['playlists']['items']:
                    results.append(self._format_playlist(playlist))
            
            return results
            
        except Exception as e:
            logger.error(f"Spotify 搜索失败: {e}")
            return []
    
    def _format_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """格式化曲目数据"""
        return {
            'id': track.get('id', ''),
            'type': 'track',
            'platform': 'spotify',
            'title': track.get('name', ''),
            'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
            'album': track.get('album', {}).get('name', '') if track.get('album') else '',
            'duration': track.get('duration_ms', 0) // 1000,
            'popularity': track.get('popularity', 0),
            'preview_url': track.get('preview_url'),
            'external_url': track.get('external_urls', {}).get('spotify'),
            'cover_url': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
            'release_date': track.get('album', {}).get('release_date') if track.get('album') else None,
            'explicit': track.get('explicit', False),
            'available_markets': track.get('available_markets', [])
        }
    
    def _format_album(self, album: Dict[str, Any]) -> Dict[str, Any]:
        """格式化专辑数据"""
        return {
            'id': album.get('id', ''),
            'type': 'album',
            'platform': 'spotify',
            'title': album.get('name', ''),
            'artist': ', '.join([artist.get('name', '') for artist in album.get('artists', [])]),
            'album': album.get('name', ''),
            'total_tracks': album.get('total_tracks', 0),
            'popularity': 0,
            'external_url': album.get('external_urls', {}).get('spotify'),
            'cover_url': album.get('images', [{}])[0].get('url') if album.get('images') else None,
            'release_date': album.get('release_date'),
            'album_type': album.get('album_type'),
            'available_markets': album.get('available_markets', [])
        }
    
    def _format_artist(self, artist: Dict[str, Any]) -> Dict[str, Any]:
        """格式化艺术家数据"""
        return {
            'id': artist.get('id', ''),
            'type': 'artist',
            'platform': 'spotify',
            'title': artist.get('name', ''),
            'artist': artist.get('name', ''),
            'popularity': artist.get('popularity', 0),
            'followers': artist.get('followers', {}).get('total', 0),
            'genres': artist.get('genres', []),
            'external_url': artist.get('external_urls', {}).get('spotify'),
            'cover_url': artist.get('images', [{}])[0].get('url') if artist.get('images') else None
        }
    
    def _format_playlist(self, playlist: Dict[str, Any]) -> Dict[str, Any]:
        """格式化播放列表数据"""
        return {
            'id': playlist.get('id', ''),
            'type': 'playlist',
            'platform': 'spotify',
            'title': playlist.get('name', ''),
            'artist': playlist.get('owner', {}).get('display_name', '') if playlist.get('owner') else '',
            'total_tracks': playlist.get('tracks', {}).get('total', 0),
            'external_url': playlist.get('external_urls', {}).get('spotify'),
            'cover_url': playlist.get('images', [{}])[0].get('url') if playlist.get('images') else None,
            'description': playlist.get('description')
        }
    
    async def get_trending(self, region: str = "CN", limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门音乐（使用热门播放列表）"""
        try:
            # Spotify 没有直接的热门榜单 API，使用特色播放列表
            params = {
                'country': region,
                'limit': min(limit, 50)
            }
            
            response = await self._make_request("browse/featured-playlists", params)
            
            if not response or not response.get('playlists', {}).get('items'):
                return []
            
            # 获取第一个播放列表的曲目
            playlist = response['playlists']['items'][0]
            playlist_id = playlist['id']
            
            tracks_response = await self._make_request(f"playlists/{playlist_id}/tracks", {'limit': limit})
            
            if not tracks_response or not tracks_response.get('items'):
                return []
            
            results = []
            for item in tracks_response.get('items', []):
                if item.get('track') and item['track'].get('type') == 'track':
                    track_data = self._format_track(item['track'])
                    track_data['playlist_name'] = playlist.get('name', '')
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取 Spotify 热门音乐失败: {e}")
            return []
    
    async def get_artist(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """获取艺术家信息"""
        try:
            response = await self._make_request(f"artists/{artist_id}")
            if response:
                return self._format_artist(response)
            return None
            
        except Exception as e:
            logger.error(f"获取 Spotify 艺术家信息失败: {e}")
            return None
    
    async def get_album(self, album_id: str) -> Optional[Dict[str, Any]]:
        """获取专辑信息"""
        try:
            response = await self._make_request(f"albums/{album_id}")
            if response:
                album_data = self._format_album(response)
                
                # 获取专辑曲目
                tracks = []
                for track in response.get('tracks', {}).get('items', []):
                    track_data = {
                        'id': track.get('id', ''),
                        'name': track.get('name', ''),
                        'track_number': track.get('track_number', 0),
                        'duration_ms': track.get('duration_ms', 0),
                        'preview_url': track.get('preview_url'),
                        'explicit': track.get('explicit', False)
                    }
                    tracks.append(track_data)
                
                album_data['tracks'] = tracks
                return album_data
            
            return None
            
        except Exception as e:
            logger.error(f"获取 Spotify 专辑信息失败: {e}")
            return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """获取播放列表信息"""
        try:
            response = await self._make_request(f"playlists/{playlist_id}")
            if response:
                return self._format_playlist(response)
            return None
            
        except Exception as e:
            logger.error(f"获取 Spotify 播放列表信息失败: {e}")
            return None
    
    async def get_charts(self, chart_type: str = "hot", region: str = "CN", limit: int = 50) -> List[Dict[str, Any]]:
        """获取音乐榜单"""
        try:
            # 使用不同的播放列表作为榜单
            playlist_ids = {
                "hot": "37i9dQZEVXbMDoHDwVN2tF",  # Global Top 50
                "new": "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
                "trending": "37i9dQZF1DX0XUsuxWHRQd"  # RapCaviar
            }
            
            playlist_id = playlist_ids.get(chart_type, playlist_ids["hot"])
            
            response = await self._make_request(f"playlists/{playlist_id}/tracks", {'limit': min(limit, 100)})
            
            if not response or not response.get('items'):
                return []
            
            results = []
            for i, item in enumerate(response.get('items', [])[:limit]):
                if item.get('track') and item['track'].get('type') == 'track':
                    track_data = self._format_track(item['track'])
                    track_data['rank'] = i + 1
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取 Spotify 榜单失败: {e}")
            return []

