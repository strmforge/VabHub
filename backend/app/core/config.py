"""
应用配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import os
import json


# ==================== Plugin Hub 源配置模型（PLUGIN-HUB-4） ====================

class PluginHubSourceConfig(BaseModel):
    """
    插件 Hub 源配置
    
    用于配置多个插件市场来源
    """
    id: str = Field(..., description="Hub 唯一 ID，如 official / infinitypacer")
    name: str = Field(..., description="展示名称，如 VabHub 官方插件市场")
    url: str = Field(..., description="plugins.json URL")
    channel: Literal["official", "community"] = Field(
        default="community", 
        description="频道类型：official 官方 / community 社区"
    )
    enabled: bool = Field(default=True, description="是否启用")
    icon_url: Optional[str] = Field(default=None, description="图标 URL")
    description: Optional[str] = Field(default=None, description="描述")


class Settings(BaseSettings):
    """
    VabHub 应用配置
    
    配置优先级：环境变量 > .env 文件 > 默认值
    详见 docs/CONFIG_OVERVIEW.md
    """
    
    # ==================== Core & Database ====================
    # 核心配置：应用基础、数据库、Redis、安全密钥
    # 详见 docs/CONFIG_OVERVIEW.md §2.1
    
    # 应用基础配置
    APP_NAME: str = "VabHub"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Demo 模式（RELEASE-1 R3）
    # 启用后禁止外部下载/网盘操作，显示 Demo 横幅
    APP_DEMO_MODE: bool = os.getenv("APP_DEMO_MODE", "false").lower() == "true"
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8080")
    
    # Web 前端基础地址（用于 Telegram Bot 生成跳转链接）
    WEB_BASE_URL: str = Field(
        default="http://localhost:5173",
        description="VabHub 前端根地址，用于在 Bot 等地方生成跳转链接",
        env="APP_WEB_BASE_URL",
    )
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8092"))  # 默认8092，避免与NAS/下载器/媒体库端口冲突（5000,5001,6000,6001,8000,8001,8080,8096等）
    WORKERS: int = 4
    
    # 数据库配置（默认使用SQLite，开发环境推荐）
    # 生产环境可以使用PostgreSQL: postgresql://vabhub:vabhub@localhost:5432/vabhub
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./vabhub.db"  # 开发环境使用SQLite
    )
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    RSSHUB_ENABLED: bool = os.getenv("RSSHUB_ENABLED", "true").lower() == "true"
    RSSHUB_BASE_URL: str = os.getenv("RSSHUB_BASE_URL", "https://rsshub.app")
    
    # 安全配置
    # 注意：这些默认值会在首次启动时被SecretManager自动替换为随机生成的密钥
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    JWT_SECRET_KEY: str = "change-this-to-a-random-jwt-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    API_TOKEN: Optional[str] = None  # API令牌（用于STRM重定向等，首次启动时自动生成）
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # 双宽带网络支持 - 自动检测本地IP
        "http://192.168.51.101:5173",
        "http://192.168.50.108:5173",
    ]
    
    # ==================== 存储 & 媒体库路径 ====================
    # 各类媒体库和存储路径配置
    # 详见 docs/CONFIG_OVERVIEW.md §2.2
    
    # 文件存储
    STORAGE_PATH: str = "./data"
    TEMP_PATH: str = "./tmp"
    MAX_UPLOAD_SIZE: int = 10737418240  # 10GB
    
    # 电子书库配置
    EBOOK_LIBRARY_ROOT: str = os.getenv("EBOOK_LIBRARY_ROOT", "./data/ebooks")  # 电子书库根目录
    
    # 视频媒体库根目录配置（用户自定义，可以是任意路径，如 /115/电影、/115/电视剧 等）
    MOVIE_LIBRARY_ROOT: str = os.getenv("MOVIE_LIBRARY_ROOT", "./data/library/movies")  # 电影媒体库根目录
    TV_LIBRARY_ROOT: str = os.getenv("TV_LIBRARY_ROOT", "./data/library/tv")  # 电视剧媒体库根目录
    ANIME_LIBRARY_ROOT: str = os.getenv("ANIME_LIBRARY_ROOT", "./data/library/anime")  # 动漫媒体库根目录
    SHORT_DRAMA_LIBRARY_ROOT: Optional[str] = os.getenv("SHORT_DRAMA_LIBRARY_ROOT", None)  # 短剧媒体库根目录（如果为 None，默认使用 TV_LIBRARY_ROOT）
    COMIC_LIBRARY_ROOT: str = os.getenv("COMIC_LIBRARY_ROOT", "./data/library/comics")  # 漫画媒体库根目录
    MUSIC_LIBRARY_ROOT: str = os.getenv("MUSIC_LIBRARY_ROOT", "./data/library/music")  # 音乐媒体库根目录（用户可设置为任意路径，如 /115/音乐、/mnt/media/Music 等）
    
    # 小说上传配置（Dev 用）
    NOVEL_UPLOAD_ROOT: str = os.getenv("NOVEL_UPLOAD_ROOT", "./data/novel_uploads")  # 小说上传根目录
    
    # ==================== TTS & 有声书 ====================
    # 文本转语音和有声书相关配置
    # --- Novel / TTS ---
    SMART_TTS_ENABLED: bool = os.getenv("SMART_TTS_ENABLED", "false").lower() == "true"  # 是否启用 TTS（文本转语音）
    SMART_TTS_PROVIDER: str = os.getenv("SMART_TTS_PROVIDER", "dummy")  # TTS 提供商：dummy/http/edge_tts 等
    SMART_TTS_DEFAULT_VOICE: Optional[str] = os.getenv("SMART_TTS_DEFAULT_VOICE", None)  # 默认语音，如 "zh-CN-female-1"
    SMART_TTS_MAX_CHAPTERS: int = int(os.getenv("SMART_TTS_MAX_CHAPTERS", "200"))  # 防止一次性小说章节太多
    SMART_TTS_CHAPTER_STRATEGY: str = os.getenv("SMART_TTS_CHAPTER_STRATEGY", "per_chapter")  # "per_chapter" | "all_in_one"
    SMART_TTS_OUTPUT_ROOT: str = os.getenv("SMART_TTS_OUTPUT_ROOT", "./data/tts_output")  # TTS 临时音频文件输出目录
    
    # TTS 存储阈值配置
    SMART_TTS_STORAGE_WARN_SIZE_GB: float = float(os.getenv("SMART_TTS_STORAGE_WARN_SIZE_GB", "10.0"))  # 警告阈值（GB）
    SMART_TTS_STORAGE_CRITICAL_SIZE_GB: float = float(os.getenv("SMART_TTS_STORAGE_CRITICAL_SIZE_GB", "30.0"))  # 危险阈值（GB）
    
    # TTS 存储自动清理配置
    SMART_TTS_STORAGE_AUTO_ENABLED: bool = os.getenv("SMART_TTS_STORAGE_AUTO_ENABLED", "false").lower() == "true"  # 是否启用自动清理
    SMART_TTS_STORAGE_AUTO_MIN_INTERVAL_HOURS: float = float(os.getenv("SMART_TTS_STORAGE_AUTO_MIN_INTERVAL_HOURS", "12.0"))  # 最小间隔（小时）
    SMART_TTS_STORAGE_AUTO_ONLY_WHEN_ABOVE_WARN: bool = os.getenv("SMART_TTS_STORAGE_AUTO_ONLY_WHEN_ABOVE_WARN", "true").lower() == "true"  # 是否只在 warn 级别以上执行
    SMART_TTS_STORAGE_AUTO_DRY_RUN: bool = os.getenv("SMART_TTS_STORAGE_AUTO_DRY_RUN", "true").lower() == "true"  # 自动模式默认是否 dry_run
    
    # TTS 限流配置
    SMART_TTS_RATE_LIMIT_ENABLED: bool = os.getenv("SMART_TTS_RATE_LIMIT_ENABLED", "false").lower() == "true"  # 是否启用 TTS 限流（默认关闭，向后兼容）
    SMART_TTS_MAX_DAILY_REQUESTS: int = int(os.getenv("SMART_TTS_MAX_DAILY_REQUESTS", "0"))  # 每日最大请求次数（按 synthesize 调用次数统计），0 或以下表示不限制
    SMART_TTS_MAX_DAILY_CHARACTERS: int = int(os.getenv("SMART_TTS_MAX_DAILY_CHARACTERS", "0"))  # 每日最大字符数（按 TTSRequest.text 长度统计），0 或以下表示不限制
    SMART_TTS_MAX_REQUESTS_PER_RUN: int = int(os.getenv("SMART_TTS_MAX_REQUESTS_PER_RUN", "0"))  # 单次 pipeline 运行内最多 TTS 请求次数（防止一次 INBOX 扫描打爆），0 或以下表示不限制
    
    # TTS Job Runner 配置
    SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN: int = int(os.getenv("SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN", "5"))  # 批量执行时每次最多处理的 Job 数量
    SMART_TTS_JOB_RUNNER_ENABLED: bool = os.getenv("SMART_TTS_JOB_RUNNER_ENABLED", "false").lower() == "true"  # 是否启用 TTS Job Runner（默认关闭，向后兼容）
    
    # HTTP TTS Provider 配置
    SMART_TTS_HTTP_ENABLED: bool = os.getenv("SMART_TTS_HTTP_ENABLED", "false").lower() == "true"  # 可选，用于额外控制
    SMART_TTS_HTTP_BASE_URL: Optional[str] = os.getenv("SMART_TTS_HTTP_BASE_URL", None)  # HTTP TTS 服务基础 URL，如 "https://example.com/tts"
    SMART_TTS_HTTP_METHOD: str = os.getenv("SMART_TTS_HTTP_METHOD", "POST")  # HTTP 方法："POST" / "GET"
    SMART_TTS_HTTP_TIMEOUT: int = int(os.getenv("SMART_TTS_HTTP_TIMEOUT", "15"))  # 请求超时时间（秒）
    SMART_TTS_HTTP_HEADERS: Optional[str] = os.getenv("SMART_TTS_HTTP_HEADERS", None)  # 请求头（JSON 字符串形式），如 '{"Authorization": "Bearer token"}'
    SMART_TTS_HTTP_BODY_TEMPLATE: Optional[str] = os.getenv("SMART_TTS_HTTP_BODY_TEMPLATE", None)  # 请求体模板（JSON 字符串），如 '{"text": "{text}", "language": "{language}"}'
    SMART_TTS_HTTP_RESPONSE_MODE: str = os.getenv("SMART_TTS_HTTP_RESPONSE_MODE", "binary")  # 响应模式："binary" | "json_base64"
    SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD: str = os.getenv("SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD", "audio")  # json_base64 模式时，响应 JSON 中音频字段名
    
    # 统一待整理收件箱配置
    INBOX_ROOT: str = os.getenv("INBOX_ROOT", "./data/inbox")  # 统一待整理目录，用户可以把各种媒体文件丢到这里
    INBOX_ENABLE_VIDEO: bool = os.getenv("INBOX_ENABLE_VIDEO", "true").lower() == "true"  # 是否启用视频（movie/tv/anime）自动识别和处理
    INBOX_ENABLE_EBOOK: bool = os.getenv("INBOX_ENABLE_EBOOK", "true").lower() == "true"  # 是否启用电子书自动识别和处理
    INBOX_ENABLE_AUDIOBOOK: bool = os.getenv("INBOX_ENABLE_AUDIOBOOK", "true").lower() == "true"  # 是否启用有声书自动识别和处理
    INBOX_ENABLE_NOVEL_TXT: bool = os.getenv("INBOX_ENABLE_NOVEL_TXT", "true").lower() == "true"  # 是否启用小说 TXT 自动识别和处理
    INBOX_ENABLE_COMIC: bool = os.getenv("INBOX_ENABLE_COMIC", "false").lower() == "true"  # 是否启用漫画自动识别和处理（预留）
    INBOX_ENABLE_MUSIC: bool = os.getenv("INBOX_ENABLE_MUSIC", "false").lower() == "true"  # 是否启用音乐自动识别和处理（预留）
    INBOX_DETECTION_MIN_SCORE: float = float(os.getenv("INBOX_DETECTION_MIN_SCORE", "0.4"))  # 检测阈值，低于此值的结果判为 unknown
    INBOX_SCAN_MAX_ITEMS: int = int(os.getenv("INBOX_SCAN_MAX_ITEMS", "500"))  # 一次扫描的最大项目数限制，防止扫描超大目录
    INBOX_PT_CATEGORY_DETECTOR_ENABLED: bool = os.getenv("INBOX_PT_CATEGORY_DETECTOR_ENABLED", "true").lower() == "true"  # 是否启用 PT 分类检测器
    
    # HNR检测配置
    HNR_SIGNATURE_PACK_PATH: str = ""  # 留空则使用默认路径
    
    # 下载器标签配置（用于标识VabHub添加的下载任务）
    TORRENT_TAG: str = os.getenv("TORRENT_TAG", "VABHUB")  # 默认标签为VABHUB
    
    # ==================== 深度学习 & 推荐系统 ====================
    # 推荐算法、GPU 加速、A/B 测试等
    # 详见 docs/CONFIG_OVERVIEW.md §3.2
    
    # 深度学习推荐系统配置
    DEEP_LEARNING_ENABLED: bool = os.getenv("DEEP_LEARNING_ENABLED", "true").lower() == "true"
    DEEP_LEARNING_GPU_ENABLED: bool = os.getenv("DEEP_LEARNING_GPU_ENABLED", "true").lower() == "true"
    DEEP_LEARNING_MODEL_TYPE: str = os.getenv("DEEP_LEARNING_MODEL_TYPE", "ncf")  # ncf, deepfm, autoencoder
    DEEP_LEARNING_EMBEDDING_DIM: int = int(os.getenv("DEEP_LEARNING_EMBEDDING_DIM", "64"))
    DEEP_LEARNING_HIDDEN_DIMS: str = os.getenv("DEEP_LEARNING_HIDDEN_DIMS", "128,64,32")  # 逗号分隔
    DEEP_LEARNING_DROPOUT_RATE: float = float(os.getenv("DEEP_LEARNING_DROPOUT_RATE", "0.2"))
    DEEP_LEARNING_LEARNING_RATE: float = float(os.getenv("DEEP_LEARNING_LEARNING_RATE", "0.001"))
    DEEP_LEARNING_BATCH_SIZE: int = int(os.getenv("DEEP_LEARNING_BATCH_SIZE", "256"))
    DEEP_LEARNING_EPOCHS: int = int(os.getenv("DEEP_LEARNING_EPOCHS", "100"))
    DEEP_LEARNING_EARLY_STOPPING_PATIENCE: int = int(os.getenv("DEEP_LEARNING_EARLY_STOPPING_PATIENCE", "10"))
    DEEP_LEARNING_MODEL_PATH: str = os.getenv("DEEP_LEARNING_MODEL_PATH", "./models/deep_learning")
    
    # 实时推荐系统配置
    REALTIME_RECOMMENDATION_ENABLED: bool = os.getenv("REALTIME_RECOMMENDATION_ENABLED", "true").lower() == "true"
    REALTIME_BUFFER_SIZE: int = int(os.getenv("REALTIME_BUFFER_SIZE", "10000"))
    REALTIME_SESSION_TIMEOUT_MINUTES: int = int(os.getenv("REALTIME_SESSION_TIMEOUT_MINUTES", "30"))
    REALTIME_UPDATE_INTERVAL_MINUTES: int = int(os.getenv("REALTIME_UPDATE_INTERVAL_MINUTES", "5"))
    REALTIME_BATCH_SIZE: int = int(os.getenv("REALTIME_BATCH_SIZE", "100"))
    REALTIME_TIME_DECAY_FACTOR: float = float(os.getenv("REALTIME_TIME_DECAY_FACTOR", "0.95"))
    REALTIME_FEATURE_CACHE_TTL: int = int(os.getenv("REALTIME_FEATURE_CACHE_TTL", "3600"))
    
    # A/B测试配置
    AB_TESTING_ENABLED: bool = os.getenv("AB_TESTING_ENABLED", "true").lower() == "true"
    AB_TESTING_MIN_SAMPLE_SIZE: int = int(os.getenv("AB_TESTING_MIN_SAMPLE_SIZE", "100"))
    AB_TESTING_SIGNIFICANCE_LEVEL: float = float(os.getenv("AB_TESTING_SIGNIFICANCE_LEVEL", "0.05"))
    AB_TESTING_EVALUATION_K: int = int(os.getenv("AB_TESTING_EVALUATION_K", "10"))
    
    # API配置
    API_PREFIX: str = "/api/v1"  # 恢复 /v1 前缀以兼容测试脚本
    TEST_ALL_REPORT_PATH: str = os.getenv(
        "TEST_ALL_REPORT_PATH",
        "./reports/test_all-latest.json",
    )
    
    # ================== Intel / Shared Intelligence 配置 ==================
    # 注意：INTEL_ENABLED 和 INTEL_MODE 在下方 Local Intel 配置中统一定义
    # INTEL_ENABLED: 控制整个 Intel 系统（包括 Local 和 Cloud）
    # INTEL_MODE: 控制使用哪种模式（local/cloud/hybrid）
    INTEL_SCHEDULER_ENDPOINT: str = os.getenv("INTEL_SCHEDULER_ENDPOINT", "https://mesh.hbnetwork.top")
    INTEL_INTEL_ENDPOINT: str = os.getenv("INTEL_INTEL_ENDPOINT", "https://intel.hbnetwork.top")
    INTEL_SNAPSHOT_BASE_URL: str = os.getenv("INTEL_SNAPSHOT_BASE_URL", "https://snap.hbnetwork.top")
    INTEL_FALLBACK_TO_LOCAL: bool = os.getenv("INTEL_FALLBACK_TO_LOCAL", "true").lower() == "true"
    
    # TMDB API配置（用户需要自己申请和配置）
    # 优先从加密存储读取，如果没有则使用环境变量
    _tmdb_api_key: Optional[str] = None
    @property
    def TMDB_API_KEY(self) -> str:
        """获取TMDB API Key（优先从加密存储读取）"""
        if self._tmdb_api_key is None:
            try:
                from app.core.api_key_manager import get_api_key_manager
                api_key_manager = get_api_key_manager()
                self._tmdb_api_key = api_key_manager.get_tmdb_api_key(
                    default=os.getenv("TMDB_API_KEY", "")
                )
            except Exception:
                self._tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        return self._tmdb_api_key
    
    # TVDB API配置
    # 优先从加密存储读取，如果没有则使用环境变量/默认值
    _tvdb_api_key: Optional[str] = None
    _tvdb_api_pin: Optional[str] = None
    @property
    def TVDB_V4_API_KEY(self) -> str:
        """获取TVDB API Key（优先从加密存储读取）"""
        if self._tvdb_api_key is None:
            try:
                from app.core.api_key_manager import get_api_key_manager
                api_key_manager = get_api_key_manager()
                self._tvdb_api_key = api_key_manager.get_tvdb_api_key(
                    default=os.getenv("TVDB_V4_API_KEY", "ed2aa66b-7899-4677-92a7-67bc9ce3d93a")
                )
            except Exception:
                self._tvdb_api_key = os.getenv("TVDB_V4_API_KEY", "ed2aa66b-7899-4677-92a7-67bc9ce3d93a")
        return self._tvdb_api_key
    
    @property
    def TVDB_V4_API_PIN(self) -> str:
        """获取TVDB API PIN（优先从加密存储读取）"""
        if self._tvdb_api_pin is None:
            try:
                from app.core.api_key_manager import get_api_key_manager
                api_key_manager = get_api_key_manager()
                self._tvdb_api_pin = api_key_manager.get_tvdb_api_pin(
                    default=os.getenv("TVDB_V4_API_PIN", "")
                )
            except Exception:
                self._tvdb_api_pin = os.getenv("TVDB_V4_API_PIN", "")
        return self._tvdb_api_pin
    
    # Fanart API配置
    # 优先从加密存储读取，如果没有则使用环境变量/默认值
    _fanart_api_key: Optional[str] = None
    @property
    def FANART_API_KEY(self) -> str:
        """获取Fanart API Key（优先从加密存储读取）"""
        if self._fanart_api_key is None:
            try:
                from app.core.api_key_manager import get_api_key_manager
                api_key_manager = get_api_key_manager()
                self._fanart_api_key = api_key_manager.get_fanart_api_key(
                    default=os.getenv("FANART_API_KEY", "d2d31f9ecabea050fc7d68aa3146015f")
                )
            except Exception:
                self._fanart_api_key = os.getenv("FANART_API_KEY", "d2d31f9ecabea050fc7d68aa3146015f")
        return self._fanart_api_key
    
    # OpenSubtitles API配置
    OPENSUBTITLES_API_KEY: str = os.getenv("OPENSUBTITLES_API_KEY", "")
    OPENSUBTITLES_USERNAME: str = os.getenv("OPENSUBTITLES_USERNAME", "")
    OPENSUBTITLES_PASSWORD: str = os.getenv("OPENSUBTITLES_PASSWORD", "")
    
    # OCR配置（用于PT站点签到验证码识别）
    OCR_HOST: str = os.getenv("OCR_HOST", "https://movie-pilot.org")  # OCR服务地址
    OCR_USE_LOCAL: bool = os.getenv("OCR_USE_LOCAL", "false").lower() == "true"  # 是否优先使用本地OCR
    
    # ==================== 基础设置 ====================
    # 访问域名（用于发送通知时，添加快捷跳转地址）
    APP_DOMAIN: str = os.getenv("APP_DOMAIN", "")
    # 识别数据源（themoviedb/douban）
    RECOGNIZE_SOURCE: str = os.getenv("RECOGNIZE_SOURCE", "themoviedb")
    # API_TOKEN 已移到安全配置部分，使用动态获取（见下方动态属性）
    # 背景壁纸来源（tmdb/bing/mediaserver/customize/none）
    WALLPAPER: str = os.getenv("WALLPAPER", "tmdb")
    # 自定义壁纸API URL
    CUSTOMIZE_WALLPAPER_API_URL: Optional[str] = os.getenv("CUSTOMIZE_WALLPAPER_API_URL", None)
    # 媒体服务器同步间隔（小时）
    MEDIASERVER_SYNC_INTERVAL: Optional[int] = int(os.getenv("MEDIASERVER_SYNC_INTERVAL", "6")) if os.getenv("MEDIASERVER_SYNC_INTERVAL") else 6
    # Github Token（用于访问Github API）
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN", None)
    
    # ==================== 高级设置 - 系统 ====================
    # 用户辅助认证（允许外部服务进行登录认证以及自动创建用户）
    AUXILIARY_AUTH_ENABLE: bool = os.getenv("AUXILIARY_AUTH_ENABLE", "false").lower() == "true"
    # 全局图片缓存（将媒体图片缓存到本地）
    GLOBAL_IMAGE_CACHE: bool = os.getenv("GLOBAL_IMAGE_CACHE", "false").lower() == "true"
    # 全局图片缓存保留天数
    GLOBAL_IMAGE_CACHE_DAYS: int = int(os.getenv("GLOBAL_IMAGE_CACHE_DAYS", "7"))
    # 分享订阅数据（分享订阅统计数据到热门订阅）
    SUBSCRIBE_STATISTIC_SHARE: bool = os.getenv("SUBSCRIBE_STATISTIC_SHARE", "true").lower() == "true"
    # 分享工作流数据（分享工作流统计数据到热门工作流）
    WORKFLOW_STATISTIC_SHARE: bool = os.getenv("WORKFLOW_STATISTIC_SHARE", "true").lower() == "true"
    # 上报插件安装数据（上报插件安装数据给服务器）
    PLUGIN_STATISTIC_SHARE: bool = os.getenv("PLUGIN_STATISTIC_SHARE", "true").lower() == "true"
    # 大内存模式（使用更大的内存缓存数据）
    BIG_MEMORY_MODE: bool = os.getenv("BIG_MEMORY_MODE", "false").lower() == "true"
    # 数据库WAL模式（仅SQLite）
    DB_WAL_ENABLE: bool = os.getenv("DB_WAL_ENABLE", "true").lower() == "true"
    # 自动更新VabHub（false/release/dev）
    VABHUB_AUTO_UPDATE: str = os.getenv("VABHUB_AUTO_UPDATE", "false")
    # 自动更新站点资源（重启时自动检测和更新站点资源包）
    AUTO_UPDATE_RESOURCE: bool = os.getenv("AUTO_UPDATE_RESOURCE", "true").lower() == "true"
    
    # ==================== 高级设置 - 媒体 ====================
    # TMDB API域名
    TMDB_API_DOMAIN: str = os.getenv("TMDB_API_DOMAIN", "api.themoviedb.org")
    # TMDB图片域名
    TMDB_IMAGE_DOMAIN: str = os.getenv("TMDB_IMAGE_DOMAIN", "image.tmdb.org")
    # TMDB元数据语言
    TMDB_LOCALE: str = os.getenv("TMDB_LOCALE", "zh")
    # 元数据缓存过期时间（小时，0为自动）
    META_CACHE_EXPIRE: int = int(os.getenv("META_CACHE_EXPIRE", "0"))
    # 刮削跟随TMDB
    SCRAP_FOLLOW_TMDB: bool = os.getenv("SCRAP_FOLLOW_TMDB", "true").lower() == "true"
    # Fanart启用
    FANART_ENABLE: bool = os.getenv("FANART_ENABLE", "false").lower() == "true"
    # Fanart语言（逗号分隔）
    FANART_LANG: str = os.getenv("FANART_LANG", "zh,en")
    # 刮削使用TMDB原始语种图片
    TMDB_SCRAP_ORIGINAL_IMAGE: Optional[bool] = None
    if os.getenv("TMDB_SCRAP_ORIGINAL_IMAGE"):
        TMDB_SCRAP_ORIGINAL_IMAGE = os.getenv("TMDB_SCRAP_ORIGINAL_IMAGE").lower() == "true"
    
    # ==================== 高级设置 - 网络 ====================
    # Github代理
    GITHUB_PROXY: Optional[str] = os.getenv("GITHUB_PROXY", None)
    # PIP代理
    PIP_PROXY: Optional[str] = os.getenv("PIP_PROXY", None)
    # 安全图片域名列表（JSON数组字符串）
    SECURITY_IMAGE_DOMAINS: List[str] = []
    if os.getenv("SECURITY_IMAGE_DOMAINS"):
        try:
            SECURITY_IMAGE_DOMAINS = json.loads(os.getenv("SECURITY_IMAGE_DOMAINS"))
        except:
            SECURITY_IMAGE_DOMAINS = []
    
    # ==================== 高级设置 - 日志 ====================
    # 日志文件最大大小（MB）
    LOG_MAX_FILE_SIZE: str = os.getenv("LOG_MAX_FILE_SIZE", "5")
    # 日志备份数量
    LOG_BACKUP_COUNT: str = os.getenv("LOG_BACKUP_COUNT", "3")
    # 日志文件格式
    LOG_FILE_FORMAT: str = os.getenv("LOG_FILE_FORMAT", "【%(levelname)s】%(asctime)s - %(message)s")
    
    # ==================== 高级设置 - 实验室 ====================
    # 插件自动重载
    PLUGIN_AUTO_RELOAD: bool = os.getenv("PLUGIN_AUTO_RELOAD", "false").lower() == "true"
    PLUGIN_REMOTE_INSTALL_ENABLED: bool = os.getenv("PLUGIN_REMOTE_INSTALL_ENABLED", "false").lower() == "true"
    PLUGIN_REMOTE_ALLOWED_HOSTS: List[str] = []
    if os.getenv("PLUGIN_REMOTE_ALLOWED_HOSTS"):
        try:
            PLUGIN_REMOTE_ALLOWED_HOSTS = json.loads(os.getenv("PLUGIN_REMOTE_ALLOWED_HOSTS"))
        except json.JSONDecodeError:
            PLUGIN_REMOTE_ALLOWED_HOSTS = [host.strip() for host in os.getenv("PLUGIN_REMOTE_ALLOWED_HOSTS", "").split(",") if host.strip()]
    PLUGIN_INSTALL_MAX_BYTES: int = int(os.getenv("PLUGIN_INSTALL_MAX_BYTES", "262144"))
    # 编码检测性能模式
    ENCODING_DETECTION_PERFORMANCE_MODE: bool = os.getenv("ENCODING_DETECTION_PERFORMANCE_MODE", "true").lower() == "true"
    
    # 网络代理配置（用于TMDB、Github等需要代理的服务）
    PROXY_HOST: Optional[str] = os.getenv("PROXY_HOST", None)  # 代理服务器地址，格式：http(s)://ip:port 或 socks5://ip:port
    DOH_ENABLE: bool = os.getenv("DOH_ENABLE", "false").lower() == "true"  # 是否启用DNS over HTTPS
    DOH_DOMAINS: str = os.getenv("DOH_DOMAINS", "api.themoviedb.org,api.tmdb.org,webservice.fanart.tv,api.github.com,github.com")  # DOH域名列表
    DOH_RESOLVERS: str = os.getenv("DOH_RESOLVERS", "1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112")  # DOH解析服务器列表
    
    # 字幕下载配置
    SUBTITLE_AUTO_DOWNLOAD: bool = os.getenv("SUBTITLE_AUTO_DOWNLOAD", "false").lower() == "true"  # 是否自动下载字幕（默认关闭）
    SUBTITLE_DEFAULT_LANGUAGE: str = os.getenv("SUBTITLE_DEFAULT_LANGUAGE", "zh")  # 默认字幕语言
    
    # 日志配置
    LOG_DIR: str = "./logs"
    LOG_MAX_SIZE: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 10
    
    # 备份系统配置
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./backups")
    AUTO_BACKUP_ENABLED: bool = os.getenv("AUTO_BACKUP_ENABLED", "true").lower() == "true"
    AUTO_BACKUP_INTERVAL_HOURS: int = int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24"))
    MAX_BACKUPS: int = int(os.getenv("MAX_BACKUPS", "10"))
    BACKUP_COMPRESSION_ENABLED: bool = os.getenv("BACKUP_COMPRESSION_ENABLED", "true").lower() == "true"
    BACKUP_VERIFY_ENABLED: bool = os.getenv("BACKUP_VERIFY_ENABLED", "true").lower() == "true"
    
    # ================== Smart Subsystem (Local Intel / External Indexer / AI Site Adapter) ==================
    # 
    # 智能子系统配置说明：
    # - Local Intel: 本地智能大脑，提供 HR 保护、站点防风控、站内信监控等功能
    # - External Indexer: 外部索引桥接，集成外部 PT 索引引擎的搜索能力
    # - AI Site Adapter: 站点 AI 适配，通过 LLM 自动生成站点适配配置
    #
    # 推荐运行模式（详见 docs/SMART_MODES_OVERVIEW.md）：
    # - 纯本地模式：INTEL_ENABLED=true, EXTERNAL_INDEXER_ENABLED=false, AI_ADAPTER_ENABLED=false
    # - 增强模式：INTEL_ENABLED=true, EXTERNAL_INDEXER_ENABLED=true, AI_ADAPTER_ENABLED=true
    # - 实验模式：全部开启，适合对自动适配感兴趣的用户
    #
    
    # --- Local Intel 配置 ---
    # INTEL_ENABLED: 控制整个 Intel 系统（包括 Local 和 Cloud）
    # 推荐默认值：true（生产环境建议开启，提供基础 HR 保护）
    INTEL_ENABLED: bool = os.getenv("INTEL_ENABLED", "true").lower() == "true"
    
    # INTEL_MODE: 控制使用哪种模式（local/cloud/hybrid）
    # 推荐默认值：local（纯本地模式，无外网依赖）
    INTEL_MODE: str = os.getenv("INTEL_MODE", "local")
    
    # INTEL_HR_GUARD_ENABLED: 控制 Local Intel 的 HR 保护功能
    # 推荐默认值：true（自动将 MOVE 操作转为 COPY，避免 HR）
    INTEL_HR_GUARD_ENABLED: bool = os.getenv("INTEL_HR_GUARD_ENABLED", "true").lower() == "true"
    
    # INTEL_SITE_GUARD_ENABLED: 控制 Local Intel 的站点防风控功能
    # 推荐默认值：true（监控站点访问频率，避免触发风控）
    INTEL_SITE_GUARD_ENABLED: bool = os.getenv("INTEL_SITE_GUARD_ENABLED", "true").lower() == "true"
    
    # --- External Indexer 配置 ---
    # EXTERNAL_INDEXER_ENABLED: 是否启用外部索引桥接
    # 推荐默认值：false（生产环境默认关闭，需要配置外部索引服务）
    EXTERNAL_INDEXER_ENABLED: bool = os.getenv("EXTERNAL_INDEXER_ENABLED", "false").lower() == "true"
    
    # EXTERNAL_INDEXER_MODULE: 外部索引模块路径（如 "external_indexer_engine.core"）
    # 推荐默认值：None（需要用户自行配置）
    EXTERNAL_INDEXER_MODULE: Optional[str] = os.getenv("EXTERNAL_INDEXER_MODULE", None)
    
    # EXTERNAL_INDEXER_MIN_RESULTS: 最小结果阈值（如果本地索引结果 >= 此值，不补充外部索引）
    # 推荐默认值：20（增强模式建议调高到 10，减少外部调用频率）
    EXTERNAL_INDEXER_MIN_RESULTS: int = int(os.getenv("EXTERNAL_INDEXER_MIN_RESULTS", "20"))
    
    # EXTERNAL_INDEXER_TIMEOUT_SECONDS: 外部索引请求超时时间（秒）
    # 推荐默认值：15（生产环境建议保持默认）
    EXTERNAL_INDEXER_TIMEOUT_SECONDS: int = int(os.getenv("EXTERNAL_INDEXER_TIMEOUT_SECONDS", "15"))
    
    # --- AI Site Adapter 配置 ---
    # AI_ADAPTER_ENABLED: 是否启用站点 AI 适配
    # 推荐默认值：true（生产环境建议开启，但需要部署 Cloudflare Pages 适配器）
    AI_ADAPTER_ENABLED: bool = os.getenv("AI_ADAPTER_ENABLED", "true").lower() == "true"
    
    # AI_ADAPTER_ENDPOINT: Cloudflare Pages API 端点
    # 推荐默认值：https://vabhub-cf-adapter.pages.dev/api/site-adapter（官方默认端点）
    AI_ADAPTER_ENDPOINT: str = os.getenv(
        "AI_ADAPTER_ENDPOINT",
        "https://vabhub-cf-adapter.pages.dev/api/site-adapter"
    )
    
    # AI_ADAPTER_TIMEOUT_SECONDS: API 请求超时时间（秒）
    # 推荐默认值：30（生产环境建议保持默认）
    AI_ADAPTER_TIMEOUT_SECONDS: int = int(os.getenv("AI_ADAPTER_TIMEOUT_SECONDS", "30"))
    
    # AI_ADAPTER_MAX_HTML_BYTES: 发送给 LLM 的 HTML 最大字节数
    # 推荐默认值：100000（约 100KB，生产环境建议保持默认）
    AI_ADAPTER_MAX_HTML_BYTES: int = int(os.getenv("AI_ADAPTER_MAX_HTML_BYTES", "100000"))
    
    # AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES: 同一站点两次自动分析的最小间隔（分钟）
    # 推荐默认值：60（增强模式建议调高到 120，减少分析频率）
    AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES: int = int(os.getenv("AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES", "60"))
    
    # --- 电子书元数据增强配置 ---
    # SMART_EBOOK_METADATA_ENABLED: 是否启用电子书元数据增强（从外部数据源补全电子书信息）
    # 推荐默认值：false（默认关闭，开启后可能访问外部服务，涉及隐私）
    # 注意：此功能需要访问外部 API（如 Open Library、Google Books 等），默认关闭以保证隐私安全
    SMART_EBOOK_METADATA_ENABLED: bool = os.getenv("SMART_EBOOK_METADATA_ENABLED", "false").lower() == "true"
    
    # SMART_EBOOK_METADATA_TIMEOUT: 元数据服务请求超时时间（秒）
    # 推荐默认值：5（生产环境建议保持默认，避免阻塞入库流程）
    SMART_EBOOK_METADATA_TIMEOUT: int = int(os.getenv("SMART_EBOOK_METADATA_TIMEOUT", "5"))
    
    # SMART_EBOOK_METADATA_PROVIDERS: 启用的元数据提供者列表（逗号分隔）
    # 可选值：dummy（本地测试）、openlibrary（Open Library API）、googlebooks（Google Books API）
    # 推荐默认值：dummy（仅用于测试，不访问外部服务）
    # 示例：SMART_EBOOK_METADATA_PROVIDERS="dummy,openlibrary"
    SMART_EBOOK_METADATA_PROVIDERS: str = os.getenv("SMART_EBOOK_METADATA_PROVIDERS", "dummy")
    
    # ==================== 插件系统配置 (DEV-SDK-1) ====================
    # PLUGINS_DIR: 插件根目录（相对项目根或绝对路径）
    PLUGINS_DIR: str = os.getenv("APP_PLUGINS_DIR", "plugins")
    
    # PLUGINS_AUTO_SCAN: 启动时是否自动扫描插件目录
    PLUGINS_AUTO_SCAN: bool = os.getenv("APP_PLUGINS_AUTO_SCAN", "true").lower() == "true"
    
    # PLUGINS_AUTO_LOAD: 启动时是否自动加载已启用的插件
    PLUGINS_AUTO_LOAD: bool = os.getenv("APP_PLUGINS_AUTO_LOAD", "true").lower() == "true"
    
    # PLUGIN_HUB_URL: 插件索引（Plugin Hub）JSON 地址
    # 默认指向官方 vabhub-plugins 仓库
    PLUGIN_HUB_URL: Optional[str] = os.getenv(
        "APP_PLUGIN_HUB_URL",
        "https://raw.githubusercontent.com/strmforge/vabhub-plugins/main/plugins.json"
    )
    
    # PLUGIN_HUB_CACHE_TTL: 插件索引缓存时间（秒），默认 30 分钟
    PLUGIN_HUB_CACHE_TTL: int = int(os.getenv("APP_PLUGIN_HUB_CACHE_TTL", "1800"))
    
    # PLUGIN_GIT_ALLOWED_HOSTS: 允许通过一键安装/更新访问的 Git 主机列表
    # 用于安全限制，避免从任意地址克隆代码
    PLUGIN_GIT_ALLOWED_HOSTS: list[str] = [
        h.strip() for h in 
        os.getenv("APP_PLUGIN_GIT_ALLOWED_HOSTS", "github.com,gitee.com").split(",")
        if h.strip()
    ]
    
    # PLUGIN_GIT_DEFAULT_BRANCH: 当未指定分支时使用的默认分支名
    # 留空则由 git 使用仓库默认分支
    PLUGIN_GIT_DEFAULT_BRANCH: Optional[str] = os.getenv("APP_PLUGIN_GIT_DEFAULT_BRANCH", None)
    
    # PLUGIN_COMMUNITY_VISIBLE: 是否在 Plugin Hub 中展示社区插件
    PLUGIN_COMMUNITY_VISIBLE: bool = os.getenv("APP_PLUGIN_COMMUNITY_VISIBLE", "true").lower() in ("true", "1", "yes")
    
    # PLUGIN_COMMUNITY_INSTALL_ENABLED: 是否允许一键安装/更新社区插件
    # 若为 False，则社区插件只能通过安装指南手动部署
    PLUGIN_COMMUNITY_INSTALL_ENABLED: bool = os.getenv("APP_PLUGIN_COMMUNITY_INSTALL_ENABLED", "true").lower() in ("true", "1", "yes")
    
    # PLUGIN_OFFICIAL_ORGS: 官方组织列表（用于自动判定 channel）
    # repo_url 中包含这些 org 的插件会被自动判定为 official
    PLUGIN_OFFICIAL_ORGS: list[str] = [
        o.strip().lower() for o in 
        os.getenv("APP_PLUGIN_OFFICIAL_ORGS", "strmforge").split(",")
        if o.strip()
    ]
    
    # PLUGIN_HUB_SOURCES: 插件 Hub 源列表（用于多市场聚合）
    # 为空时回退到单一 PLUGIN_HUB_URL
    # 格式：JSON 数组字符串，如 [{"id":"official","name":"VabHub 官方插件市场","url":"https://...","channel":"official"}]
    _PLUGIN_HUB_SOURCES_RAW: Optional[str] = os.getenv("APP_PLUGIN_HUB_SOURCES", None)
    
    @property
    def PLUGIN_HUB_SOURCES(self) -> list[PluginHubSourceConfig]:
        """
        获取插件 Hub 源列表
        
        优先使用 APP_PLUGIN_HUB_SOURCES 环境变量（JSON 数组）；
        若为空，回退到 PLUGIN_HUB_URL 构造默认官方源。
        """
        # 尝试解析 JSON 配置
        if self._PLUGIN_HUB_SOURCES_RAW:
            try:
                raw_list = json.loads(self._PLUGIN_HUB_SOURCES_RAW)
                if isinstance(raw_list, list) and raw_list:
                    return [PluginHubSourceConfig(**item) for item in raw_list]
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # 解析失败，使用默认值
                pass
        
        # 回退：从 PLUGIN_HUB_URL 构造默认官方源
        if self.PLUGIN_HUB_URL:
            return [
                PluginHubSourceConfig(
                    id="official",
                    name="VabHub 官方插件市场",
                    url=self.PLUGIN_HUB_URL,
                    channel="official",
                    enabled=True,
                    description="VabHub 官方维护的插件索引",
                )
            ]
        
        return []
    
    # ==================== DOWNLOAD-CENTER-UI-2 配置 ====================
    # VABHUB_TORRENT_LABELS: VabHub 管理的种子标签白名单
    # 用于判断下载任务是否由 VabHub 管理
    VABHUB_TORRENT_LABELS: List[str] = os.getenv(
        "VABHUB_TORRENT_LABELS", 
        "vabhub,moviepilot,auto"
    ).split(",") if os.getenv("VABHUB_TORRENT_LABELS") else ["vabhub", "moviepilot", "auto"]
    
    # ==================== Telegram Bot 配置 ====================
    # TELEGRAM_BOT_TOKEN: Telegram Bot Token（从 @BotFather 获取）
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN", None)
    
    # TELEGRAM_BOT_WEBHOOK_URL: Webhook URL（可选，用于 Webhook 模式）
    TELEGRAM_BOT_WEBHOOK_URL: Optional[str] = os.getenv("TELEGRAM_BOT_WEBHOOK_URL", None)
    
    # TELEGRAM_BOT_ENABLED: 是否启用 Telegram Bot
    TELEGRAM_BOT_ENABLED: bool = os.getenv("TELEGRAM_BOT_ENABLED", "false").lower() in ("true", "1", "yes")
    
    # TELEGRAM_BOT_PROXY: 代理地址（可选），例如 http://127.0.0.1:7890
    TELEGRAM_BOT_PROXY: Optional[str] = os.getenv("TELEGRAM_BOT_PROXY", None)
    
    # TELEGRAM_BOT_ALLOWED_USERS: 允许绑定的用户白名单（可选），逗号分隔的用户ID或用户名
    TELEGRAM_BOT_ALLOWED_USERS: Optional[str] = os.getenv("TELEGRAM_BOT_ALLOWED_USERS", None)
    
    # ==================== 通知推送配置 ====================
    # NOTIFY_TELEGRAM_DOWNLOAD_SUBSCRIPTION: 订阅命中通知是否推送到 Telegram
    NOTIFY_TELEGRAM_DOWNLOAD_SUBSCRIPTION: bool = os.getenv("NOTIFY_TELEGRAM_DOWNLOAD_SUBSCRIPTION", "false").lower() in ("true", "1", "yes")
    
    # NOTIFY_TELEGRAM_DOWNLOAD_COMPLETION: 下载完成通知是否推送到 Telegram
    NOTIFY_TELEGRAM_DOWNLOAD_COMPLETION: bool = os.getenv("NOTIFY_TELEGRAM_DOWNLOAD_COMPLETION", "false").lower() in ("true", "1", "yes")
    
    # NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK: HR 风险通知是否推送到 Telegram
    NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK: bool = os.getenv("NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK", "true").lower() in ("true", "1", "yes")
    
    # ==================== 媒体库跳转配置 ====================
    # 用于电视墙海报点击的 LAN/WAN 智能路由
    # 详见 docs/TV_WALL_PLAYBACK_OVERVIEW.md §2.5
    
    # MEDIA_LIBRARY_TYPE: 媒体库类型，支持 emby/jellyfin/none
    MEDIA_LIBRARY_TYPE: Literal["emby", "jellyfin", "none"] = os.getenv("MEDIA_LIBRARY_TYPE", "none")
    
    # MEDIA_LIBRARY_BASE_URL: 媒体库 Web 基础地址，例如 http://emby.lan:8096
    MEDIA_LIBRARY_BASE_URL: Optional[str] = os.getenv("MEDIA_LIBRARY_BASE_URL", None)
    
    # MEDIA_LIBRARY_SEARCH_PATH_TEMPLATE: 搜索页路径模板，{query} 会被替换为编码后的搜索词
    MEDIA_LIBRARY_SEARCH_PATH_TEMPLATE: str = os.getenv("MEDIA_LIBRARY_SEARCH_PATH_TEMPLATE", "/web/index.html#!/search.html?query={query}")
    
    # LAN_CIDR_LIST: 内网网段列表，用于判断请求是否来自内网
    LAN_CIDR_LIST: List[str] = Field(
        default=["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
        description="内网网段列表，逗号分隔"
    )
    
    # FORCE_LAN_MODE: 强制 LAN 模式（用于开发测试）
    FORCE_LAN_MODE: bool = os.getenv("FORCE_LAN_MODE", "false").lower() in ("true", "1", "yes")

    # ==================== AI Orchestrator ====================
    # AI 总控层：外部 LLM + 本地 AI 器官的只读编排
    # 驱动 AI 订阅助手、AI 故障医生、AI 整理顾问、AI 阅读助手
    # 详见 docs/CONFIG_OVERVIEW.md §3.1 和 docs/FUTURE_AI_OVERVIEW.md
    # 
    # AI 总控层配置，用于外部 LLM + 本地 AI 器官的只读编排
    
    # 总控开关：是否启用 AI Orchestrator
    AI_ORCH_ENABLED: bool = os.getenv("AI_ORCH_ENABLED", "false").lower() in ("true", "1", "yes")
    
    # LLM 提供者类型：目前仅支持 "http"
    AI_ORCH_LLM_PROVIDER: str = os.getenv("AI_ORCH_LLM_PROVIDER", "http")
    
    # LLM API 端点 URL（如 OpenAI 兼容的 API 地址）
    AI_ORCH_LLM_ENDPOINT: Optional[str] = os.getenv("AI_ORCH_LLM_ENDPOINT", None)
    
    # LLM API Key
    AI_ORCH_LLM_API_KEY: Optional[str] = os.getenv("AI_ORCH_LLM_API_KEY", None)
    
    # LLM 模型名称（如 gpt-4o-mini, qwen-plus 等）
    AI_ORCH_LLM_MODEL: Optional[str] = os.getenv("AI_ORCH_LLM_MODEL", None)
    
    # LLM 请求超时时间（秒）
    AI_ORCH_LLM_TIMEOUT: int = int(os.getenv("AI_ORCH_LLM_TIMEOUT", "30"))
    
    # LLM 最大 token 数
    AI_ORCH_LLM_MAX_TOKENS: int = int(os.getenv("AI_ORCH_LLM_MAX_TOKENS", "2048"))
    
    # 调试日志开关：是否记录 plan / tool 调用摘要
    AI_ORCH_DEBUG_LOG: bool = os.getenv("AI_ORCH_DEBUG_LOG", "false").lower() in ("true", "1", "yes")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def PROXY(self) -> Optional[dict]:
        """
        获取代理配置（用于requests/httpx）
        返回格式：{"http://": "http://proxy:port", "https://": "http://proxy:port"}
        """
        if self.PROXY_HOST:
            return {
                "http://": self.PROXY_HOST,
                "https://": self.PROXY_HOST,
            }
        return None
    
    @property
    def PROXY_FOR_HTTPX(self) -> Optional[str]:
        """
        获取代理配置（用于httpx.AsyncClient）
        返回格式：http://proxy:port 或 socks5://proxy:port
        """
        return self.PROXY_HOST
    
    # ==================== 动态密钥属性（首次启动时自动生成） ====================
    # 这些属性会在首次访问时自动从SecretManager获取或生成密钥
    _secret_key: Optional[str] = None
    _jwt_secret_key: Optional[str] = None
    _api_token: Optional[str] = None
    
    @property
    def SECRET_KEY_DYNAMIC(self) -> str:
        """动态获取SECRET_KEY（首次启动时自动生成）"""
        if self._secret_key is None:
            try:
                from app.core.secret_manager import get_secret_manager
                manager = get_secret_manager()
                self._secret_key = manager.get_secret_key()
            except Exception as e:
                from loguru import logger
                logger.warning(f"获取SECRET_KEY失败，使用默认值: {e}")
                self._secret_key = self.SECRET_KEY
        return self._secret_key
    
    @property
    def JWT_SECRET_KEY_DYNAMIC(self) -> str:
        """动态获取JWT_SECRET_KEY（首次启动时自动生成）"""
        if self._jwt_secret_key is None:
            try:
                from app.core.secret_manager import get_secret_manager
                manager = get_secret_manager()
                self._jwt_secret_key = manager.get_jwt_secret_key()
            except Exception as e:
                from loguru import logger
                logger.warning(f"获取JWT_SECRET_KEY失败，使用默认值: {e}")
                self._jwt_secret_key = self.JWT_SECRET_KEY
        return self._jwt_secret_key
    
    @property
    def API_TOKEN_DYNAMIC(self) -> str:
        """动态获取API_TOKEN（首次启动时自动生成）"""
        if self._api_token is None:
            try:
                from app.core.secret_manager import get_secret_manager
                manager = get_secret_manager()
                self._api_token = manager.get_api_token()
            except Exception as e:
                from loguru import logger
                logger.warning(f"获取API_TOKEN失败: {e}")
                self._api_token = None
        return self._api_token or ""


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取应用配置实例
    
    用于 FastAPI 的依赖注入
    """
    return settings

