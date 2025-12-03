"""
工作流引擎
"""
from typing import Dict, List, Optional, Any
from loguru import logger
import asyncio


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, db=None):
        self.db = db
        self.action_handlers = {
            "send_notification": self._handle_send_notification,
            "create_download": self._handle_create_download,
            "update_subscription": self._handle_update_subscription,
            "execute_command": self._handle_execute_command,
            "webhook": self._handle_webhook,
            "delay": self._handle_delay,
            "condition": self._handle_condition,
            # RSSHub相关动作
            "create_subscription": self._handle_create_subscription,
            "create_music_subscription": self._handle_create_music_subscription,
            "search_and_download": self._handle_search_and_download,
            "detect_media_type": self._handle_detect_media_type,
            "add_to_queue": self._handle_add_to_queue,
        }
    
    async def execute(self, workflow: Any, context: Dict = None) -> Dict:
        """
        执行工作流
        
        Args:
            workflow: 工作流对象
            context: 执行上下文
            
        Returns:
            执行结果
        """
        context = context or {}
        results = []
        
        try:
            actions = workflow.actions if isinstance(workflow.actions, list) else []
            
            if not actions:
                return {
                    "success": False,
                    "error": "工作流没有动作"
                }
            
            logger.info(f"开始执行工作流: {workflow.name}, 动作数: {len(actions)}")
            
            for index, action in enumerate(actions):
                action_type = action.get("type")
                action_config = action.get("config", {})
                
                if action_type not in self.action_handlers:
                    logger.warning(f"未知的动作类型: {action_type}")
                    results.append({
                        "action": action_type,
                        "success": False,
                        "error": f"未知的动作类型: {action_type}"
                    })
                    continue
                
                try:
                    # 执行动作
                    handler = self.action_handlers[action_type]
                    result = await handler(action_config, context)
                    
                    results.append({
                        "action": action_type,
                        "success": result.get("success", True),
                        "result": result.get("result"),
                        "error": result.get("error")
                    })
                    
                    # 如果动作失败且配置了失败时停止，则停止执行
                    if not result.get("success") and action_config.get("stop_on_failure", False):
                        logger.warning(f"动作 {action_type} 执行失败，停止工作流执行")
                        break
                    
                    # 更新上下文
                    if result.get("context"):
                        context.update(result["context"])
                
                except Exception as e:
                    logger.error(f"执行动作 {action_type} 失败: {e}")
                    results.append({
                        "action": action_type,
                        "success": False,
                        "error": str(e)
                    })
                    
                    if action_config.get("stop_on_failure", False):
                        break
            
            success = all(r.get("success", False) for r in results)
            
            return {
                "success": success,
                "results": results,
                "context": context
            }
        
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": results
            }
    
    async def _handle_send_notification(self, config: Dict, context: Dict) -> Dict:
        """发送通知动作"""
        from app.modules.notification.channel_manager import NotificationChannelManager
        
        title = config.get("title", "") or context.get("title", "")
        message = config.get("message", "") or context.get("message", "")
        notification_type = config.get("type", "info")
        channels = config.get("channels", ["system"])
        
        # 从上下文或配置中获取渠道配置
        metadata = {}
        if config.get("email_config"):
            metadata["email_config"] = config["email_config"]
        if config.get("telegram_config"):
            metadata["telegram_config"] = config["telegram_config"]
        if config.get("wechat_config"):
            metadata["wechat_config"] = config["wechat_config"]
        if config.get("webhook_config"):
            metadata["webhook_config"] = config["webhook_config"]
        
        logger.info(f"发送通知: {title} - {message} (渠道: {channels})")
        
        try:
            # 直接使用渠道管理器发送通知（不依赖数据库）
            channel_manager = NotificationChannelManager()
            results = await channel_manager.send(
                title=title,
                message=message,
                notification_type=notification_type,
                channels=channels,
                metadata=metadata if metadata else None
            )
            
            # 检查发送结果
            success = all(r.get("success", False) for r in results.values())
            
            return {
                "success": success,
                "result": {
                    "title": title,
                    "message": message,
                    "channels": channels,
                    "send_results": results
                }
            }
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_create_download(self, config: Dict, context: Dict) -> Dict:
        """创建下载动作"""
        # TODO: 实现下载创建逻辑
        title = config.get("title") or context.get("title", "")
        magnet_link = config.get("magnet_link") or context.get("magnet_link", "")
        downloader = config.get("downloader", "qBittorrent")
        
        logger.info(f"创建下载: {title} (下载器: {downloader})")
        
        # 这里应该调用DownloadService创建下载任务
        # from app.modules.download.service import DownloadService
        # download_service = DownloadService(self.db)
        # result = await download_service.create_download({...})
        
        return {
            "success": True,
            "result": {"title": title, "downloader": downloader},
            "context": {"download_id": "mock_download_id"}
        }
    
    async def _handle_update_subscription(self, config: Dict, context: Dict) -> Dict:
        """更新订阅动作"""
        # TODO: 实现订阅更新逻辑
        subscription_id = config.get("subscription_id") or context.get("subscription_id")
        updates = config.get("updates", {})
        
        logger.info(f"更新订阅: {subscription_id}, 更新内容: {updates}")
        
        return {
            "success": True,
            "result": {"subscription_id": subscription_id, "updates": updates}
        }
    
    async def _handle_execute_command(self, config: Dict, context: Dict) -> Dict:
        """执行命令动作"""
        command = config.get("command", "")
        
        logger.info(f"执行命令: {command}")
        
        # TODO: 实现命令执行逻辑（需要谨慎处理，避免安全风险）
        # 可以使用subprocess执行系统命令
        
        return {
            "success": True,
            "result": {"command": command, "output": "命令执行完成"}
        }
    
    async def _handle_webhook(self, config: Dict, context: Dict) -> Dict:
        """Webhook动作"""
        import httpx
        
        url = config.get("url", "")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        data = config.get("data", {})
        
        logger.info(f"发送Webhook: {method} {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers, timeout=10.0)
                elif method.upper() == "GET":
                    response = await client.get(url, params=data, headers=headers, timeout=10.0)
                else:
                    return {
                        "success": False,
                        "error": f"不支持的HTTP方法: {method}"
                    }
                
                return {
                    "success": response.is_success,
                    "result": {
                        "status_code": response.status_code,
                        "response": response.text[:500]  # 限制响应长度
                    }
                }
        except Exception as e:
            logger.error(f"Webhook请求失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_delay(self, config: Dict, context: Dict) -> Dict:
        """延迟动作"""
        seconds = config.get("seconds", 1)
        
        logger.info(f"延迟 {seconds} 秒")
        await asyncio.sleep(seconds)
        
        return {
            "success": True,
            "result": {"delay_seconds": seconds}
        }
    
    async def _handle_condition(self, config: Dict, context: Dict) -> Dict:
        """条件判断动作"""
        condition = config.get("condition", "")
        condition_type = config.get("type", "expression")  # expression, comparison
        
        # TODO: 实现条件判断逻辑
        # 可以支持简单的表达式或比较
        
        result = True  # 默认通过
        
        if condition_type == "comparison":
            field = config.get("field", "")
            operator = config.get("operator", "eq")  # eq, ne, gt, lt, gte, lte
            value = config.get("value")
            
            field_value = context.get(field)
            
            if operator == "eq":
                result = field_value == value
            elif operator == "ne":
                result = field_value != value
            elif operator == "gt":
                result = field_value > value
            elif operator == "lt":
                result = field_value < value
            elif operator == "gte":
                result = field_value >= value
            elif operator == "lte":
                result = field_value <= value
        
        logger.info(f"条件判断: {condition}, 结果: {result}")
        
        return {
            "success": True,
            "result": {"condition": condition, "result": result},
            "context": {"condition_passed": result}
        }
    
    async def _handle_create_subscription(self, config: Dict, context: Dict) -> Dict:
        """创建订阅动作（RSSHub工作流）"""
        if not self.db:
            logger.warning("工作流引擎未提供数据库会话，无法创建订阅")
            return {
                "success": False,
                "error": "数据库会话未提供"
            }
        
        try:
            from app.modules.subscription.service import SubscriptionService
            
            media_type = config.get("media_type", "movie")
            match_mode = config.get("match_mode", "title_year")
            auto_download = config.get("auto_download", True)
            quality_rules = config.get("quality_rules", {})
            
            # 从上下文获取媒体信息
            media_info = context.get('media_info', {})
            title = context.get('title') or media_info.get('title', '')
            year = context.get('year') or media_info.get('year')
            
            if not title:
                return {
                    "success": False,
                    "error": "缺少媒体标题"
                }
            
            # 构建订阅数据
            subscription_data = {
                "title": title,
                "media_type": media_type,
                "year": year,
                "enabled": True,
                "auto_download": auto_download
            }
            
            # 添加质量规则
            if quality_rules:
                if quality_rules.get("min_resolution"):
                    subscription_data["resolution"] = quality_rules["min_resolution"]
                if quality_rules.get("preferred_effects"):
                    subscription_data["effect"] = ",".join(quality_rules["preferred_effects"])
            
            # 创建订阅
            subscription_service = SubscriptionService(self.db)
            subscription = await subscription_service.create_subscription(subscription_data)
            
            logger.info(f"RSSHub工作流创建订阅成功: {title} (ID: {subscription.id})")
            
            return {
                "success": True,
                "result": {
                    "subscription_id": subscription.id,
                    "title": title
                },
                "context": {"subscription_id": subscription.id}
            }
        except Exception as e:
            logger.error(f"创建订阅失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_create_music_subscription(self, config: Dict, context: Dict) -> Dict:
        """创建音乐订阅动作（RSSHub工作流）"""
        if not self.db:
            logger.warning("工作流引擎未提供数据库会话，无法创建音乐订阅")
            return {
                "success": False,
                "error": "数据库会话未提供"
            }
        
        try:
            from app.modules.music.service import MusicService
            
            match_mode = config.get("match_mode", "title_artist")
            auto_download = config.get("auto_download", False)
            platform = config.get("platform", "all")
            
            # 从上下文获取媒体信息
            media_info = context.get('media_info', {})
            title = context.get('title') or media_info.get('title', '')
            
            if not title:
                return {
                    "success": False,
                    "error": "缺少音乐标题"
                }
            
            # 构建音乐订阅数据
            subscription_data = {
                "name": title,
                "platform": platform,
                "enabled": True,
                "auto_download": auto_download
            }
            
            # 创建音乐订阅
            music_service = MusicService(self.db)
            subscription = await music_service.create_subscription(subscription_data)
            
            logger.info(f"RSSHub工作流创建音乐订阅成功: {title} (ID: {subscription.id})")
            
            return {
                "success": True,
                "result": {
                    "subscription_id": subscription.id,
                    "name": title
                },
                "context": {"music_subscription_id": subscription.id}
            }
        except Exception as e:
            logger.error(f"创建音乐订阅失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_search_and_download(self, config: Dict, context: Dict) -> Dict:
        """搜索并下载动作（RSSHub工作流）"""
        if not self.db:
            logger.warning("工作流引擎未提供数据库会话，无法搜索下载")
            return {
                "success": False,
                "error": "数据库会话未提供"
            }
        
        try:
            from app.modules.search.service import SearchService
            from app.modules.download.service import DownloadService
            
            sites = config.get("sites", "all")
            min_seeders = config.get("min_seeders", 5)
            
            # 从上下文获取媒体信息
            media_info = context.get('media_info', {})
            title = context.get('title') or media_info.get('title', '')
            year = context.get('year') or media_info.get('year')
            season = context.get('season') or media_info.get('season')
            episode = context.get('episode') or media_info.get('episode')
            
            if not title:
                return {
                    "success": False,
                    "error": "缺少媒体标题"
                }
            
            # 构建搜索查询
            query = title
            if year:
                query += f" {year}"
            if season and episode:
                query += f" S{season:02d}E{episode:02d}"
            
            # 执行搜索
            search_service = SearchService(self.db)
            search_result = await search_service.search(
                query=query,
                media_type=context.get('media_type', 'video'),
                min_seeders=min_seeders,
                sites=sites if sites != "all" else None
            )
            
            if not search_result or not search_result.get('items'):
                logger.warning(f"RSSHub工作流搜索无结果: {query}")
                return {
                    "success": False,
                    "error": "搜索无结果"
                }
            
            # 选择第一个结果进行下载
            first_result = search_result['items'][0]
            
            # 创建下载任务
            download_service = DownloadService(self.db)
            download_task = await download_service.create_download({
                "title": first_result.get('title', title),
                "magnet_link": first_result.get('magnet', ''),
                "downloader": "qBittorrent",
                "user_id": context.get('user_id')
            })
            
            logger.info(f"RSSHub工作流搜索并下载成功: {title} (下载任务ID: {download_task.id})")
            
            return {
                "success": True,
                "result": {
                    "download_id": download_task.id,
                    "search_query": query,
                    "selected_result": first_result.get('title')
                },
                "context": {"download_id": download_task.id}
            }
        except Exception as e:
            logger.error(f"搜索并下载失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_detect_media_type(self, config: Dict, context: Dict) -> Dict:
        """检测媒体类型动作（RSSHub工作流）"""
        from app.modules.rsshub.media_extractor import RSSHubMediaExtractor
        
        fallback = config.get("fallback", "video")
        
        # 从上下文获取RSS项
        rss_item = context.get('rss_item', {})
        title = rss_item.get('title', '') or context.get('title', '')
        
        if not title:
            return {
                "success": True,
                "result": {"media_type": fallback},
                "context": {"media_type": fallback}
            }
        
        # 提取媒体信息
        extractor = RSSHubMediaExtractor()
        media_info = extractor.extract_media_info(title)
        
        detected_type = media_info.get('type', fallback)
        
        logger.info(f"RSSHub工作流检测媒体类型: {title} -> {detected_type}")
        
        return {
            "success": True,
            "result": {"media_type": detected_type, "media_info": media_info},
            "context": {
                "media_type": detected_type,
                "media_info": media_info
            }
        }
    
    async def _handle_add_to_queue(self, config: Dict, context: Dict) -> Dict:
        """添加到队列动作（RSSHub工作流）"""
        queue_type = config.get("queue_type", "general")
        tag = config.get("tag", "RSSHub")
        
        # 从上下文获取信息
        title = context.get('title', '')
        media_type = context.get('media_type', 'video')
        
        logger.info(f"RSSHub工作流添加到队列: {title} (类型: {queue_type}, 标签: {tag})")
        
        # TODO: 实现队列系统
        # 目前仅记录日志，等待队列系统实现
        
        return {
            "success": True,
            "result": {
                "queue_type": queue_type,
                "tag": tag,
                "title": title
            },
            "context": {"queued": True}
        }

