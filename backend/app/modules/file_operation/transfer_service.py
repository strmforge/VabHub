"""
文件整理服务
整合TransferHandler，根据transfer_type执行整理
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.file_operation.transfer_handler import TransferHandler
from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
from app.modules.strm.file_operation_mode import FileOperationMode, FileOperationConfig
from app.schemas.directory import DirectoryConfig
from app.modules.global_rules import GlobalRulesService


class TransferService:
    """文件整理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.global_rules_service = GlobalRulesService(db)  # 全局规则服务缓存实例
    
    async def transfer_file(
        self,
        source_path: str,
        target_path: str,
        directory_config: DirectoryConfig,
        media_info: Optional[Dict[str, Any]] = None,
        overwrite_mode: str = "never"
    ) -> Dict[str, Any]:
        """
        整理文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            directory_config: 目录配置
            media_info: 媒体信息（可选）
            overwrite_mode: 覆盖模式（never/always/size/latest）
        
        Returns:
            整理结果
        """
        try:
            # P3-3: SafetyPolicyEngine 移动前检查
            try:
                from app.modules.safety.engine import get_safety_policy_engine
                from app.modules.safety.models import SafetyContext
                from app.modules.hr_case.repository import get_hr_repository
                
                safety_engine = get_safety_policy_engine()
                hr_repo = get_hr_repository()
                
                # 尝试从路径或媒体信息中提取站点和种子信息
                site_key = None
                torrent_id = None
                hr_case = None
                
                if media_info:
                    site_key = media_info.get('site_key')
                    torrent_id = media_info.get('torrent_id')
                
                if site_key and torrent_id:
                    hr_case = await hr_repo.get_by_site_and_torrent(site_key, torrent_id)
                
                # 创建安全上下文
                safety_ctx = SafetyContext(
                    action="move",
                    site_key=site_key,
                    torrent_id=torrent_id,
                    trigger="user_web",
                    hr_case=hr_case,
                    metadata={
                        "source_path": source_path,
                        "target_path": target_path,
                        "changes_seeding_path": self._check_if_affects_seeding_path(source_path, target_path)
                    }
                )
                
                # 执行安全策略评估
                safety_decision = await safety_engine.evaluate(safety_ctx)
                
                if safety_decision.decision == "DENY":
                    return {
                        "success": False,
                        "message": f"安全策略阻止移动: {safety_decision.message}",
                        "error_code": "SAFETY_BLOCKED"
                    }
                elif safety_decision.decision == "REQUIRE_CONFIRM":
                    return {
                        "success": False,
                        "message": f"需要用户确认: {safety_decision.message}",
                        "error_code": "SAFETY_REQUIRE_CONFIRM",
                        "suggested_alternative": safety_decision.suggested_alternative
                    }
                    
            except Exception as e:
                logger.warning(f"安全策略检查失败，允许移动: {e}")
            
            # 1. 确定文件操作模式
            operation_mode = self._get_operation_mode(directory_config.transfer_type)
            if not operation_mode:
                return {
                    "success": False,
                    "error": f"不支持的整理方式: {directory_config.transfer_type}"
                }
            
            # 1.5. 检查全局规则 C 档限制
            try:
                # 检测是否为 STRM 生成场景
                is_strm_generation = (operation_mode == FileOperationMode.STRM_ONLY)
                
                # 应用全局规则移动行为调整
                resolved_transfer_type = await self.global_rules_service.resolve_move_behavior(
                    directory_config.transfer_type,
                    is_strm_generation=is_strm_generation
                )
                
                if resolved_transfer_type != directory_config.transfer_type:
                    logger.warning(
                        f"全局规则C档限制: {directory_config.transfer_type} -> {resolved_transfer_type} "
                        f"(STRM场景: {is_strm_generation})"
                    )
                    # 重新确定操作模式
                    operation_mode = self._get_operation_mode(resolved_transfer_type)
                    if not operation_mode:
                        return {
                            "success": False,
                            "error": f"全局规则调整后不支持的整理方式: {resolved_transfer_type}"
                        }
            except Exception as e:
                logger.warning(f"全局规则C档检查失败，使用原始操作模式: {e}")
                # 降级处理：继续使用原始操作模式
            
            # 2. 检查 HR 保护（Local Intel）
            # 注意：开关判断已集中在 scheduler_hooks.should_keep_source_after_download 中
            should_delete_source = (operation_mode == FileOperationMode.MOVE)
            if should_delete_source:
                # 尝试从 media_info 或通过其他方式获取 site_id 和 torrent_id
                site_id = None
                torrent_id = None
                
                if media_info:
                    site_id = media_info.get("site_id") or media_info.get("site")
                    torrent_id = media_info.get("torrent_id")
                
                # 如果获取到了 site_id 和 torrent_id，检查 HR 状态（Phase 5 + Phase 8）
                if site_id and torrent_id:
                    try:
                        from app.core.config import settings
                        from app.modules.settings.service import SettingsService
                        
                        # Phase 8: 检查配置开关
                        settings_service = SettingsService(self.db)
                        intel_enabled = await settings_service.get_setting("intel_enabled", True)
                        intel_move_check_enabled = await settings_service.get_setting("intel_move_check_enabled", True)
                        
                        # 如果 Local Intel 未启用或 MOVE 检查未启用，跳过 HR 检查
                        if not (settings.INTEL_ENABLED and intel_enabled and intel_move_check_enabled):
                            logger.debug(f"LocalIntel: 已禁用或 MOVE 检查未启用，跳过 HR 保护检查")
                        else:
                            # 尝试从 app.state 获取 LocalIntelEngine
                            from fastapi import Request
                            # 注意：这里需要从请求上下文获取 engine，或者使用全局单例
                            # 为了简化，我们使用 scheduler_hooks（它内部会调用 engine）
                            from app.core.intel_local.scheduler_hooks import should_keep_source_after_download
                            keep_source = await should_keep_source_after_download(site_id, torrent_id)
                            
                            # 或者直接使用 engine（如果可用）
                            try:
                                from app.core.intel_local.factory import build_local_intel_engine
                                engine = build_local_intel_engine()
                                is_safe = await engine.is_move_safe(site_id, torrent_id)
                                keep_source = not is_safe  # is_safe=True 表示可以删除，keep_source 相反
                            except:
                                pass  # 回退到 scheduler_hooks
                            
                            if keep_source:
                                # HR 保护：不要删源，改为 COPY 或 LINK
                                logger.info(
                                    f"LocalIntel: protect source file for HR candidate torrent "
                                    f"(site={site_id}, torrent_id={torrent_id})"
                                )
                                should_delete_source = False
                                # 如果原本是 MOVE，改为 COPY（保留源文件）
                                if operation_mode == FileOperationMode.MOVE:
                                    operation_mode = FileOperationMode.COPY
                    except Exception as e:
                        logger.warning(f"LocalIntel HR 保护检查失败: {e}，继续使用原始操作模式")
            
            # 3. 创建文件操作配置
            file_operation_config = FileOperationConfig(
                source_storage=directory_config.storage,
                target_storage=directory_config.library_storage,
                operation_mode=operation_mode,
                source_path=source_path,
                target_path=target_path,
                overwrite_mode=overwrite_mode,
                delete_source=should_delete_source,
                keep_seeding=(operation_mode in [FileOperationMode.COPY, FileOperationMode.LINK, FileOperationMode.SOFTLINK])
            )
            
            # 4. 执行文件传输
            result = await TransferHandler.transfer_file(file_operation_config)
            
            # 5. 记录转移历史
            try:
                from app.modules.transfer_history.service import TransferHistoryService
                history_service = TransferHistoryService(self.db)
                
                # 获取实际的目标路径（如果result中有）
                actual_dest = result.get("target_path") or result.get("dest") or target_path
                
                # 获取文件大小
                file_size = None
                source_path_obj = Path(source_path)
                if source_path_obj.exists():
                    file_size = source_path_obj.stat().st_size
                elif result.get("file_size"):
                    file_size = result.get("file_size")
                
                await history_service.create_history(
                    src=source_path,
                    dest=actual_dest,
                    src_storage=directory_config.storage,
                    dest_storage=directory_config.library_storage,
                    mode=directory_config.transfer_type or "move",
                    media_info=media_info,
                    file_size=file_size,
                    status=result.get("success", False),
                    errmsg=result.get("error") if not result.get("success") else None
                )
            except Exception as e:
                logger.warning(f"记录转移历史失败: {e}")
            
            if result.get("success"):
                logger.info(f"文件整理成功: {source_path} -> {target_path}")
            else:
                logger.error(f"文件整理失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"文件整理异常: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transfer_directory(
        self,
        source_dir: str,
        directory_config: DirectoryConfig,
        media_info: Optional[Dict[str, Any]] = None,
        overwrite_mode: str = "never"
    ) -> Dict[str, Any]:
        """
        整理目录
        
        Args:
            source_dir: 源目录路径
            directory_config: 目录配置
            media_info: 媒体信息（可选）
            overwrite_mode: 覆盖模式
        
        Returns:
            整理结果
        """
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"源目录不存在: {source_dir}"
                }
            
            # 确定目标路径
            if directory_config.library_path:
                target_base = Path(directory_config.library_path)
            else:
                return {
                    "success": False,
                    "error": "目录配置中未指定媒体库路径"
                }
            
            # 如果是文件，直接整理
            if source_path.is_file():
                target_path = target_base / source_path.name
                return await self.transfer_file(
                    str(source_path),
                    str(target_path),
                    directory_config,
                    media_info,
                    overwrite_mode
                )
            
            # 如果是目录，整理目录中的所有文件
            results = {
                "success": True,
                "transferred_files": [],
                "failed_files": [],
                "total_count": 0,
                "success_count": 0,
                "failed_count": 0
            }
            
            # 遍历目录中的所有文件
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    results["total_count"] += 1
                    
                    # 计算相对路径
                    relative_path = file_path.relative_to(source_path)
                    target_path = target_base / relative_path
                    
                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 整理文件
                    result = await self.transfer_file(
                        str(file_path),
                        str(target_path),
                        directory_config,
                        media_info,
                        overwrite_mode
                    )
                    
                    if result.get("success"):
                        results["success_count"] += 1
                        results["transferred_files"].append({
                            "source": str(file_path),
                            "target": str(target_path)
                        })
                    else:
                        results["failed_count"] += 1
                        results["failed_files"].append({
                            "source": str(file_path),
                            "error": result.get("error")
                        })
            
            # 如果所有文件都整理成功，且是移动模式，删除源目录
            if (results["success_count"] == results["total_count"] and 
                directory_config.transfer_type == "move" and 
                source_path.is_dir()):
                try:
                    source_path.rmdir()
                    logger.info(f"源目录已删除: {source_dir}")
                except Exception as e:
                    logger.warning(f"删除源目录失败: {e}")
            
            results["success"] = results["failed_count"] == 0
            return results
            
        except Exception as e:
            logger.error(f"整理目录异常: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_operation_mode(self, transfer_type: Optional[str]) -> Optional[FileOperationMode]:
        """
        将transfer_type转换为FileOperationMode
        
        Args:
            transfer_type: 整理方式（copy/move/link/softlink）
        
        Returns:
            FileOperationMode枚举值
        """
        if not transfer_type:
            return None
        
        transfer_type_map = {
            "copy": FileOperationMode.COPY,
            "move": FileOperationMode.MOVE,
            "link": FileOperationMode.LINK,
            "softlink": FileOperationMode.SOFTLINK
        }
        
        return transfer_type_map.get(transfer_type.lower())
    
    def _check_if_affects_seeding_path(self, source_path: str, target_path: str) -> bool:
        """检查文件移动是否影响做种路径"""
        try:
            # 简单检查：如果源路径包含常见的下载目录，移动可能影响做种
            seeding_indicators = ['downloads', 'torrents', 'qbittorrent', 'transmission']
            source_lower = source_path.lower()
            
            for indicator in seeding_indicators:
                if indicator in source_lower:
                    return True
            
            return False
        except Exception:
            return False

