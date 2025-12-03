"""
QQ音乐平台客户端
集成QQ音乐API提供音乐搜索、推荐等功能
"""
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger


class QQMusicClient:
    """QQ音乐客户端"""
    
    def __init__(self):
        self.base_url = "https://c.y.qq.com"
        self.search_url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        self.toplist_url = "https://c.y.qq.com/v8/fcg-bin/fcg_myqq_toplist.fcg"
        self.song_url = "https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg"
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://y.qq.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
    
    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发起API请求"""
        try:
            # 添加通用参数
            if params is None:
                params = {}
            
            params.update({
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        text = await response.text()
                        # QQ音乐返回的可能是JSONP格式，需要处理
                        if text.startswith('callback(') and text.endswith(')'):
                            text = text[9:-1]  # 移除 callback( 和 )
                        elif text.startswith('MusicJsonCallback(') and text.endswith(')'):
                            text = text[18:-1]
                        elif text.startswith('jsonCallback(') and text.endswith(')'):
                            text = text[13:-1]
                        
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning(f"QQ音乐API返回非JSON格式: {text[:100]}")
                            return {}
                    else:
                        logger.warning(f"QQ音乐API请求失败: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"QQ音乐API请求失败: {e}")
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
                "all": 0,      # 综合搜索
                "track": 0,    # 单曲
                "album": 8,    # 专辑
                "artist": 9,   # 歌手
                "song": 0,
                "playlist": 2
            }
            
            qq_type = type_mapping.get(search_type, 0)
            
            params = {
                'ct': 24,
                'qqmusic_ver': 1298,
                'new_json': 1,
                'remoteplace': 'txt.yqq.center',
                'searchid': str(int(time.time() * 1000)),
                't': qq_type,
                'aggr': 1,
                'cr': 1,
                'catZhida': 1,
                'lossless': 0,
                'flag_qc': 0,
                'p': 1,
                'n': min(limit, 100),
                'w': query,
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0
            }
            
            response = await self._make_request(self.search_url, params)
            
            if response.get('code') != 0:
                logger.warning(f"QQ音乐搜索返回错误: {response.get('code')}")
                return []
            
            results = []
            data = response.get('data', {})
            
            # 处理单曲搜索结果
            if 'song' in data and 'list' in data['song']:
                for song in data['song']['list']:
                    track_data = self._format_track(song)
                    if track_data:
                        results.append(track_data)
            
            # 处理专辑搜索结果
            if 'album' in data and 'list' in data['album']:
                for album in data['album']['list']:
                    album_data = self._format_album(album)
                    if album_data:
                        results.append(album_data)
            
            # 处理歌手搜索结果
            if 'singer' in data and 'list' in data['singer']:
                for singer in data['singer']['list']:
                    artist_data = self._format_artist(singer)
                    if artist_data:
                        results.append(artist_data)
            
            # 处理播放列表搜索结果
            if 'playlist' in data and 'list' in data['playlist']:
                for playlist in data['playlist']['list']:
                    playlist_data = self._format_playlist(playlist)
                    if playlist_data:
                        results.append(playlist_data)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"QQ音乐搜索失败: {e}")
            return []
    
    def _format_track(self, song: Dict[str, Any]) -> Dict[str, Any]:
        """格式化曲目数据"""
        try:
            # 获取歌手名称
            singers = song.get('singer', [])
            artist_names = [singer.get('name', '') for singer in singers if singer.get('name')]
            artist = ', '.join(artist_names) if artist_names else '未知歌手'
            
            # 获取专辑信息
            album_info = song.get('album', {})
            album_name = album_info.get('name', '未知专辑') if isinstance(album_info, dict) else '未知专辑'
            
            # 构建封面图片URL
            album_mid = album_info.get('mid', '') if isinstance(album_info, dict) else ''
            image_url = f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{album_mid}.jpg" if album_mid else None
            
            return {
                'id': str(song.get('songmid', '')),
                'type': 'track',
                'platform': 'qq_music',
                'title': song.get('songname', ''),
                'artist': artist,
                'album': album_name,
                'duration': song.get('interval', 0),
                'popularity': song.get('popularity', 0),
                'preview_url': None,  # QQ音乐需要特殊处理播放链接
                'external_url': f"https://y.qq.com/n/yqq/song/{song.get('songmid', '')}.html",
                'cover_url': image_url,
                'release_date': None,
                'explicit': False,
                'songmid': song.get('songmid', ''),
                'albummid': album_mid
            }
        except Exception as e:
            logger.warning(f"格式化QQ音乐曲目数据失败: {e}")
            return {}
    
    def _format_album(self, album: Dict[str, Any]) -> Dict[str, Any]:
        """格式化专辑数据"""
        try:
            # 获取歌手名称
            singer_name = album.get('singername', '未知歌手')
            
            # 构建封面图片URL
            album_mid = album.get('albummid', '')
            image_url = f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{album_mid}.jpg" if album_mid else None
            
            return {
                'id': str(album.get('albummid', '')),
                'type': 'album',
                'platform': 'qq_music',
                'title': album.get('albumname', ''),
                'artist': singer_name,
                'album': album.get('albumname', ''),
                'total_tracks': 0,  # QQ音乐搜索结果中没有这个字段
                'popularity': 0,
                'external_url': f"https://y.qq.com/n/yqq/album/{album.get('albummid', '')}.html",
                'cover_url': image_url,
                'release_date': album.get('publictime', ''),
                'album_type': 'album',
                'albummid': album_mid
            }
        except Exception as e:
            logger.warning(f"格式化QQ音乐专辑数据失败: {e}")
            return {}
    
    def _format_artist(self, singer: Dict[str, Any]) -> Dict[str, Any]:
        """格式化艺术家数据"""
        try:
            # 构建头像URL
            singer_mid = singer.get('singermid', '')
            image_url = f"https://y.gtimg.cn/music/photo_new/T001R300x300M000{singer_mid}.jpg" if singer_mid else None
            
            return {
                'id': str(singer.get('singermid', '')),
                'type': 'artist',
                'platform': 'qq_music',
                'title': singer.get('singername', ''),
                'artist': singer.get('singername', ''),
                'popularity': 0,
                'followers': 0,
                'genres': [],
                'external_url': f"https://y.qq.com/n/yqq/singer/{singer.get('singermid', '')}.html",
                'cover_url': image_url,
                'singermid': singer_mid
            }
        except Exception as e:
            logger.warning(f"格式化QQ音乐艺术家数据失败: {e}")
            return {}
    
    def _format_playlist(self, playlist: Dict[str, Any]) -> Dict[str, Any]:
        """格式化播放列表数据"""
        try:
            pic_url = playlist.get('pic') or playlist.get('picUrl')
            if pic_url and not pic_url.startswith('http'):
                pic_url = f"https://y.gtimg.cn/music/photo_new/T001R300x300M000{pic_url}.jpg"
            
            return {
                'id': str(playlist.get('dissid', '')),
                'type': 'playlist',
                'platform': 'qq_music',
                'title': playlist.get('dissname', ''),
                'artist': playlist.get('creator', {}).get('name', '') if playlist.get('creator') else '',
                'total_tracks': playlist.get('songnum', 0),
                'external_url': f"https://y.qq.com/n/yqq/playlist/{playlist.get('dissid', '')}.html",
                'cover_url': pic_url,
                'description': playlist.get('introduction'),
                'play_count': playlist.get('listennum', 0)
            }
        except Exception as e:
            logger.warning(f"格式化QQ音乐播放列表数据失败: {e}")
            return {}
    
    async def get_trending(self, region: str = "CN", limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门音乐（排行榜）"""
        try:
            # 获取排行榜列表
            params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0
            }
            
            response = await self._make_request(self.toplist_url, params)
            
            if response.get('code') != 0 or not response.get('data', {}).get('topList'):
                return []
            
            # 获取第一个排行榜（通常是热歌榜）
            toplist = response['data']['topList'][0]
            toplist_id = toplist.get('id', 4)  # 默认使用热歌榜
            
            # 获取排行榜详情
            detail_url = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg"
            detail_params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0,
                'tpl': 3,
                'page': 'detail',
                'type': 'top',
                'topid': toplist_id,
                'num': min(limit, 100)
            }
            
            detail_response = await self._make_request(detail_url, detail_params)
            
            if detail_response.get('code') != 0:
                return []
            
            results = []
            songs = detail_response.get('songlist', [])
            
            for i, song in enumerate(songs[:limit]):
                track_data = self._format_track(song.get('data', {}))
                if track_data:
                    track_data['rank'] = song.get('cur_rank', i + 1)
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取QQ音乐热门音乐失败: {e}")
            return []
    
    async def get_charts(self, chart_type: str = "hot", region: str = "CN", limit: int = 50) -> List[Dict[str, Any]]:
        """获取音乐榜单"""
        try:
            # 不同的榜单ID
            chart_ids = {
                "hot": 4,        # 热歌榜
                "new": 27,       # 新歌榜
                "trending": 62,  # 飙升榜
                "original": 52   # 原创榜
            }
            
            chart_id = chart_ids.get(chart_type, chart_ids["hot"])
            
            detail_url = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg"
            detail_params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0,
                'tpl': 3,
                'page': 'detail',
                'type': 'top',
                'topid': chart_id,
                'num': min(limit, 100)
            }
            
            detail_response = await self._make_request(detail_url, detail_params)
            
            if detail_response.get('code') != 0:
                return []
            
            results = []
            songs = detail_response.get('songlist', [])
            
            for i, song in enumerate(songs[:limit]):
                track_data = self._format_track(song.get('data', {}))
                if track_data:
                    track_data['rank'] = song.get('cur_rank', i + 1)
                    results.append(track_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取QQ音乐榜单失败: {e}")
            return []
    
    async def get_artist(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """获取艺术家信息"""
        try:
            # QQ音乐艺术家详情API
            url = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_track_cp.fcg"
            params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0,
                'singermid': artist_id,
                'order': 'listen',
                'begin': 0,
                'num': 1  # 只获取基本信息
            }
            
            response = await self._make_request(url, params)
            
            if response.get('code') != 0:
                return None
            
            data = response.get('data', {})
            singer_info = data.get('singer_info', {})
            
            if not singer_info:
                return None
            
            return self._format_artist(singer_info)
            
        except Exception as e:
            logger.error(f"获取QQ音乐艺术家信息失败: {e}")
            return None
    
    async def get_album(self, album_id: str) -> Optional[Dict[str, Any]]:
        """获取专辑信息"""
        try:
            # QQ音乐专辑详情API
            url = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg"
            params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0,
                'albummid': album_id
            }
            
            response = await self._make_request(url, params)
            
            if response.get('code') != 0:
                return None
            
            data = response.get('data', {})
            
            if not data:
                return None
            
            # 格式化专辑信息
            album_data = self._format_album(data)
            
            # 获取专辑曲目
            tracks = []
            for song in data.get('list', []):
                track_data = {
                    'id': song.get('songmid', ''),
                    'name': song.get('songname', ''),
                    'track_number': song.get('index_album', 0),
                    'duration': song.get('interval', 0),
                    'preview_url': None,
                    'explicit': False
                }
                tracks.append(track_data)
            
            album_data['tracks'] = tracks
            album_data['total_tracks'] = len(tracks)
            
            return album_data
            
        except Exception as e:
            logger.error(f"获取QQ音乐专辑信息失败: {e}")
            return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """获取播放列表信息"""
        try:
            # QQ音乐播放列表详情API
            url = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
            params = {
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0,
                'disstid': playlist_id,
                'type': 1,
                'json': 1,
                'utf8': 1,
                'onlysong': 0,
                'new_format': 1
            }
            
            response = await self._make_request(url, params)
            
            if response.get('code') != 0:
                return None
            
            cdlist = response.get('cdlist', [])
            if not cdlist:
                return None
            
            playlist = cdlist[0]
            
            return self._format_playlist(playlist)
            
        except Exception as e:
            logger.error(f"获取QQ音乐播放列表信息失败: {e}")
            return None

