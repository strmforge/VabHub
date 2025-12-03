"""
RSSHub工作流模板定义
为每种媒体类型定义默认工作流模板
"""

from typing import Dict, Optional, List
from loguru import logger


class RSSHubWorkflowTemplate:
    """RSSHub工作流模板"""
    
    def __init__(
        self,
        template_id: str,
        name: str,
        media_type: str,
        description: str,
        actions: List[Dict]
    ):
        self.template_id = template_id
        self.name = name
        self.media_type = media_type
        self.description = description
        self.actions = actions
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "media_type": self.media_type,
            "description": self.description,
            "actions": self.actions
        }


class RSSHubWorkflowTemplateManager:
    """RSSHub工作流模板管理器"""
    
    def __init__(self):
        self.templates: Dict[str, RSSHubWorkflowTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认工作流模板"""
        # 1. 电影（video）工作流模板
        self.templates['video'] = RSSHubWorkflowTemplate(
            template_id='rsshub_video_default',
            name='RSSHub电影自动订阅',
            media_type='video',
            description='自动从RSSHub电影榜单创建订阅，按片名+年份匹配PT资源',
            actions=[
                {
                    "type": "create_subscription",
                    "config": {
                        "media_type": "movie",
                        "match_mode": "title_year",  # 按片名+年份匹配
                        "auto_download": True,
                        "quality_rules": {
                            "min_resolution": "1080p",
                            "preferred_effects": ["HDR", "Dolby Vision"]
                        }
                    }
                },
                {
                    "type": "search_and_download",
                    "config": {
                        "sites": "all",  # 使用所有站点
                        "min_seeders": 5
                    }
                }
            ]
        )
        
        # 2. 电视剧（tv）工作流模板
        self.templates['tv'] = RSSHubWorkflowTemplate(
            template_id='rsshub_tv_default',
            name='RSSHub电视剧自动订阅',
            media_type='tv',
            description='自动从RSSHub电视剧榜单创建订阅，按剧名+SxxExx匹配PT资源',
            actions=[
                {
                    "type": "create_subscription",
                    "config": {
                        "media_type": "tv",
                        "match_mode": "title_season_episode",  # 按剧名+季数+集数匹配
                        "auto_download": True,
                        "quality_rules": {
                            "min_resolution": "1080p",
                            "preferred_effects": ["HDR"]
                        }
                    }
                },
                {
                    "type": "search_and_download",
                    "config": {
                        "sites": "all",
                        "min_seeders": 5
                    }
                }
            ]
        )
        
        # 3. 综艺（variety）工作流模板
        self.templates['variety'] = RSSHubWorkflowTemplate(
            template_id='rsshub_variety_default',
            name='RSSHub综艺自动订阅',
            media_type='variety',
            description='自动从RSSHub综艺榜单创建订阅',
            actions=[
                {
                    "type": "create_subscription",
                    "config": {
                        "media_type": "tv",  # 综艺也使用tv类型
                        "match_mode": "title",
                        "auto_download": True,
                        "quality_rules": {
                            "min_resolution": "720p"
                        }
                    }
                },
                {
                    "type": "search_and_download",
                    "config": {
                        "sites": "all",
                        "min_seeders": 3
                    }
                }
            ]
        )
        
        # 4. 番剧（anime）工作流模板
        self.templates['anime'] = RSSHubWorkflowTemplate(
            template_id='rsshub_anime_default',
            name='RSSHub番剧自动订阅',
            media_type='anime',
            description='自动从RSSHub番剧榜单创建订阅，按番剧名+季数+集数匹配PT资源',
            actions=[
                {
                    "type": "create_subscription",
                    "config": {
                        "media_type": "tv",
                        "match_mode": "title_season_episode",
                        "auto_download": True,
                        "quality_rules": {
                            "min_resolution": "1080p",
                            "preferred_effects": ["HDR"]
                        }
                    }
                },
                {
                    "type": "search_and_download",
                    "config": {
                        "sites": "all",
                        "min_seeders": 5
                    }
                }
            ]
        )
        
        # 5. 音乐（music）工作流模板
        self.templates['music'] = RSSHubWorkflowTemplate(
            template_id='rsshub_music_default',
            name='RSSHub音乐自动订阅',
            media_type='music',
            description='自动从RSSHub音乐榜单创建音乐订阅（目前仅创建订阅，等待音乐功能完善）',
            actions=[
                {
                    "type": "create_music_subscription",
                    "config": {
                        "match_mode": "title_artist",
                        "auto_download": False,  # 音乐暂不自动下载
                        "platform": "all"  # 支持所有平台
                    }
                },
                {
                    "type": "add_to_queue",
                    "config": {
                        "queue_type": "music",
                        "tag": "RSSHub"
                    }
                }
            ]
        )
        
        # 6. 混合类型（mixed）工作流模板
        self.templates['mixed'] = RSSHubWorkflowTemplate(
            template_id='rsshub_mixed_default',
            name='RSSHub混合内容自动订阅',
            media_type='mixed',
            description='自动从RSSHub混合榜单创建订阅，根据内容类型自动选择处理方式',
            actions=[
                {
                    "type": "detect_media_type",
                    "config": {
                        "fallback": "video"
                    }
                },
                {
                    "type": "create_subscription",
                    "config": {
                        "media_type": "auto",  # 自动检测
                        "match_mode": "auto",
                        "auto_download": True
                    }
                }
            ]
        )
        
        logger.info(f"已初始化 {len(self.templates)} 个RSSHub工作流模板")
    
    def get_template(self, media_type: str) -> Optional[RSSHubWorkflowTemplate]:
        """
        获取指定类型的工作流模板
        
        Args:
            media_type: 媒体类型（video/tv/variety/anime/music/mixed）
            
        Returns:
            工作流模板，如果不存在返回None
        """
        return self.templates.get(media_type)
    
    def list_templates(self) -> List[RSSHubWorkflowTemplate]:
        """获取所有模板列表"""
        return list(self.templates.values())
    
    def get_template_dict(self, media_type: str) -> Optional[Dict]:
        """
        获取模板字典（用于工作流引擎）
        
        Args:
            media_type: 媒体类型
            
        Returns:
            模板字典，如果不存在返回None
        """
        template = self.get_template(media_type)
        return template.to_dict() if template else None


# 全局模板管理器实例
_template_manager: Optional[RSSHubWorkflowTemplateManager] = None


def get_workflow_template_manager() -> RSSHubWorkflowTemplateManager:
    """获取工作流模板管理器单例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = RSSHubWorkflowTemplateManager()
    return _template_manager

