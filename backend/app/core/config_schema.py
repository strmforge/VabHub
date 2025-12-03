"""
配置 Schema 定义
LAUNCH-1 L1-1 实现

用于配置校验和前端表单渲染
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class ConfigFieldType(str, Enum):
    """配置字段类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PASSWORD = "password"
    PATH = "path"
    URL = "url"
    LIST = "list"


class ConfigFieldSchema(BaseModel):
    """配置字段 Schema"""
    key: str
    label: str
    type: ConfigFieldType
    default: Any = None
    required: bool = False
    description: Optional[str] = None
    group: str = "general"
    sensitive: bool = False  # 是否敏感字段（密码、密钥等）
    env_var: Optional[str] = None  # 对应的环境变量名


class ConfigGroupSchema(BaseModel):
    """配置分组 Schema"""
    key: str
    label: str
    description: Optional[str] = None
    fields: List[ConfigFieldSchema] = []


class AppConfigSchema(BaseModel):
    """应用配置 Schema - 用于前端渲染和校验"""
    groups: List[ConfigGroupSchema] = []


# 定义配置 Schema
def get_config_schema() -> AppConfigSchema:
    """获取配置 Schema 定义"""
    return AppConfigSchema(groups=[
        # 基础配置
        ConfigGroupSchema(
            key="general",
            label="基础配置",
            description="应用基础设置",
            fields=[
                ConfigFieldSchema(
                    key="APP_NAME",
                    label="应用名称",
                    type=ConfigFieldType.STRING,
                    default="VabHub",
                    env_var="APP_NAME"
                ),
                ConfigFieldSchema(
                    key="DEBUG",
                    label="调试模式",
                    type=ConfigFieldType.BOOLEAN,
                    default=False,
                    description="生产环境请关闭",
                    env_var="DEBUG"
                ),
                ConfigFieldSchema(
                    key="LOG_LEVEL",
                    label="日志级别",
                    type=ConfigFieldType.STRING,
                    default="INFO",
                    description="可选: DEBUG, INFO, WARNING, ERROR",
                    env_var="LOG_LEVEL"
                ),
            ]
        ),
        # 数据库配置
        ConfigGroupSchema(
            key="database",
            label="数据库配置",
            description="数据库连接设置",
            fields=[
                ConfigFieldSchema(
                    key="DATABASE_URL",
                    label="数据库连接字符串",
                    type=ConfigFieldType.STRING,
                    default="sqlite:///./vabhub.db",
                    required=True,
                    description="SQLite: sqlite:///./vabhub.db, PostgreSQL: postgresql://user:pass@host:port/db",
                    env_var="DATABASE_URL",
                    sensitive=True
                ),
            ]
        ),
        # Redis 配置
        ConfigGroupSchema(
            key="redis",
            label="Redis 配置",
            description="Redis 缓存设置",
            fields=[
                ConfigFieldSchema(
                    key="REDIS_ENABLED",
                    label="启用 Redis",
                    type=ConfigFieldType.BOOLEAN,
                    default=True,
                    env_var="REDIS_ENABLED"
                ),
                ConfigFieldSchema(
                    key="REDIS_URL",
                    label="Redis 连接地址",
                    type=ConfigFieldType.URL,
                    default="redis://localhost:6379/0",
                    env_var="REDIS_URL"
                ),
            ]
        ),
        # 媒体存储路径
        ConfigGroupSchema(
            key="storage",
            label="存储路径配置",
            description="各类媒体文件存储路径",
            fields=[
                ConfigFieldSchema(
                    key="EBOOK_LIBRARY_ROOT",
                    label="电子书库路径",
                    type=ConfigFieldType.PATH,
                    default="./data/ebooks",
                    description="小说/电子书存储目录",
                    env_var="EBOOK_LIBRARY_ROOT"
                ),
                ConfigFieldSchema(
                    key="COMIC_LIBRARY_ROOT",
                    label="漫画库路径",
                    type=ConfigFieldType.PATH,
                    default="./data/library/comics",
                    description="漫画存储目录",
                    env_var="COMIC_LIBRARY_ROOT"
                ),
                ConfigFieldSchema(
                    key="MUSIC_LIBRARY_ROOT",
                    label="音乐库路径",
                    type=ConfigFieldType.PATH,
                    default="./data/library/music",
                    description="音乐存储目录",
                    env_var="MUSIC_LIBRARY_ROOT"
                ),
                ConfigFieldSchema(
                    key="SMART_TTS_OUTPUT_ROOT",
                    label="TTS 输出路径",
                    type=ConfigFieldType.PATH,
                    default="./data/tts_output",
                    description="TTS 音频文件输出目录",
                    env_var="SMART_TTS_OUTPUT_ROOT"
                ),
            ]
        ),
        # TTS 配置
        ConfigGroupSchema(
            key="tts",
            label="TTS 配置",
            description="文本转语音设置",
            fields=[
                ConfigFieldSchema(
                    key="SMART_TTS_ENABLED",
                    label="启用 TTS",
                    type=ConfigFieldType.BOOLEAN,
                    default=False,
                    env_var="SMART_TTS_ENABLED"
                ),
                ConfigFieldSchema(
                    key="SMART_TTS_PROVIDER",
                    label="TTS 提供商",
                    type=ConfigFieldType.STRING,
                    default="dummy",
                    description="可选: dummy, http, edge_tts",
                    env_var="SMART_TTS_PROVIDER"
                ),
                ConfigFieldSchema(
                    key="SMART_TTS_DEFAULT_VOICE",
                    label="默认语音",
                    type=ConfigFieldType.STRING,
                    default="",
                    env_var="SMART_TTS_DEFAULT_VOICE"
                ),
            ]
        ),
        # 下载器配置
        ConfigGroupSchema(
            key="downloaders",
            label="下载器配置",
            description="PT 下载器设置",
            fields=[
                ConfigFieldSchema(
                    key="TORRENT_TAG",
                    label="种子标签",
                    type=ConfigFieldType.STRING,
                    default="VABHUB",
                    description="VabHub 添加的下载任务标签",
                    env_var="TORRENT_TAG"
                ),
            ]
        ),
        # 外部 API 配置
        ConfigGroupSchema(
            key="external_api",
            label="外部 API 配置",
            description="第三方 API 密钥设置",
            fields=[
                ConfigFieldSchema(
                    key="TMDB_API_KEY",
                    label="TMDB API Key",
                    type=ConfigFieldType.PASSWORD,
                    default="",
                    description="用于获取影视元数据",
                    env_var="TMDB_API_KEY",
                    sensitive=True
                ),
                ConfigFieldSchema(
                    key="OPENSUBTITLES_API_KEY",
                    label="OpenSubtitles API Key",
                    type=ConfigFieldType.PASSWORD,
                    default="",
                    description="用于字幕下载",
                    env_var="OPENSUBTITLES_API_KEY",
                    sensitive=True
                ),
            ]
        ),
        # 国际化配置
        ConfigGroupSchema(
            key="i18n",
            label="国际化配置",
            description="语言和时区设置",
            fields=[
                ConfigFieldSchema(
                    key="TMDB_LOCALE",
                    label="TMDB 语言",
                    type=ConfigFieldType.STRING,
                    default="zh",
                    description="TMDB 元数据语言",
                    env_var="TMDB_LOCALE"
                ),
            ]
        ),
    ])


class ConfigValidationError(BaseModel):
    """配置校验错误"""
    field: str
    message: str


class ConfigValidationResult(BaseModel):
    """配置校验结果"""
    valid: bool
    errors: List[ConfigValidationError] = []


def validate_config(config: Dict[str, Any]) -> ConfigValidationResult:
    """
    校验配置
    
    Args:
        config: 配置字典
        
    Returns:
        校验结果
    """
    errors: List[ConfigValidationError] = []
    schema = get_config_schema()
    
    for group in schema.groups:
        for field in group.fields:
            value = config.get(field.key)
            
            # 必填校验
            if field.required and (value is None or value == ""):
                errors.append(ConfigValidationError(
                    field=field.key,
                    message=f"{field.label} 是必填项"
                ))
                continue
            
            if value is None:
                continue
            
            # 类型校验
            if field.type == ConfigFieldType.INTEGER:
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(ConfigValidationError(
                        field=field.key,
                        message=f"{field.label} 必须是整数"
                    ))
            elif field.type == ConfigFieldType.FLOAT:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(ConfigValidationError(
                        field=field.key,
                        message=f"{field.label} 必须是数字"
                    ))
            elif field.type == ConfigFieldType.BOOLEAN:
                if not isinstance(value, bool) and value not in ["true", "false", "True", "False", "1", "0"]:
                    errors.append(ConfigValidationError(
                        field=field.key,
                        message=f"{field.label} 必须是布尔值"
                    ))
            elif field.type == ConfigFieldType.URL:
                if value and not (value.startswith("http://") or value.startswith("https://") or value.startswith("redis://")):
                    errors.append(ConfigValidationError(
                        field=field.key,
                        message=f"{field.label} 必须是有效的 URL"
                    ))
    
    return ConfigValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )


def get_effective_config(mask_sensitive: bool = True) -> Dict[str, Any]:
    """
    获取当前生效的配置
    
    Args:
        mask_sensitive: 是否隐藏敏感字段
        
    Returns:
        配置字典
    """
    from app.core.config import settings
    
    schema = get_config_schema()
    result: Dict[str, Any] = {}
    
    for group in schema.groups:
        for field in group.fields:
            value = getattr(settings, field.key, field.default)
            
            # 隐藏敏感字段
            if mask_sensitive and field.sensitive and value:
                if isinstance(value, str) and len(value) > 0:
                    value = "***"
            
            result[field.key] = value
    
    return result
