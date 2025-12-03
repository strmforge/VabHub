"""
音乐平台客户端
"""
from app.core.music_clients.spotify import SpotifyClient
from app.core.music_clients.netease import NeteaseClient
from app.core.music_clients.qq_music import QQMusicClient

__all__ = [
    "SpotifyClient",
    "NeteaseClient",
    "QQMusicClient"
]

