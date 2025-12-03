"""
AI 整理顾问服务

FUTURE-AI-CLEANUP-ADVISOR-1 P3 实现
提供媒体库清理建议的核心业务逻辑
"""

from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai_cleanup_advisor import (
    CleanupPlanDraft,
    CleanupScope,
    CleanupFocus,
)
from app.core.ai_orchestrator.service import AIOrchestratorService, OrchestratorMode
from app.core.ai_orchestrator.tools.base import OrchestratorContext
from app.core.ai_orchestrator.llm_client import get_llm_client


class AICleanupAdvisorService:
    """
    AI 整理顾问服务
    
    提供媒体库清理建议功能，调用 Orchestrator CLEANUP_ADVISOR 模式
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_cleanup_plan(
        self,
        prompt: Optional[str] = None,
        scope: Optional[CleanupScope] = None,
        user_id: int = 1,
    ) -> CleanupPlanDraft:
        """
        生成清理计划草案
        
        Args:
            prompt: 用户自然语言描述（可选）
            scope: 清理范围配置
            user_id: 用户 ID
            
        Returns:
            CleanupPlanDraft 清理计划草案
        """
        try:
            # 构建清理提示
            cleanup_prompt = self._build_cleanup_prompt(prompt, scope)
            
            # 创建上下文
            context = OrchestratorContext(
                db=self.db,
                user_id=user_id,
                is_admin=True,
                debug_mode=False,
            )
            
            # 获取 LLM 客户端并创建 Orchestrator
            llm_client = get_llm_client()
            orchestrator = AIOrchestratorService(llm_client)
            
            # 调用 Orchestrator CLEANUP_ADVISOR 模式
            result = await orchestrator.run(
                context=context,
                mode=OrchestratorMode.CLEANUP_ADVISOR,
                prompt=cleanup_prompt,
            )
            
            # 解析清理计划草案
            draft = orchestrator.parse_cleanup_draft(result.llm_suggested_changes)
            
            # 如果解析失败但有 LLM 摘要，补充到草案中
            if not draft.actions and result.llm_summary:
                draft.summary = result.llm_summary[:200]
            
            return draft
            
        except Exception as e:
            logger.error(f"[ai_cleanup_advisor] 生成清理计划失败: {e}")
            return CleanupPlanDraft.fallback_draft(str(e))
    
    def _build_cleanup_prompt(
        self,
        user_prompt: Optional[str],
        scope: Optional[CleanupScope],
    ) -> str:
        """构建清理提示"""
        parts = []
        
        # 聚焦类型描述
        if scope:
            focus_desc = {
                CleanupFocus.ALL: "全面分析所有可清理内容",
                CleanupFocus.DOWNLOADS: "聚焦于已完成的下载任务",
                CleanupFocus.DUPLICATES: "聚焦于重复的媒体文件",
                CleanupFocus.LOW_QUALITY: "聚焦于低质量版本（可升级的）",
                CleanupFocus.SEEDING: "聚焦于保种任务（已完成的可清理）",
            }
            parts.append(f"分析范围：{focus_desc.get(scope.focus, '全面分析')}")
            
            if scope.min_size_gb:
                parts.append(f"仅考虑大于 {scope.min_size_gb} GB 的文件")
            
            if scope.include_risky:
                parts.append("包含高风险项（仍在保种中的内容）")
            else:
                parts.append("排除高风险项（仍在保种中的内容）")
        
        # 用户描述
        if user_prompt:
            parts.append(f"用户需求：{user_prompt}")
        else:
            parts.append("请分析存储空间使用情况，找出可以安全清理的内容并生成清理计划草案。")
        
        return "\n".join(parts)
    
    @staticmethod
    def get_preset_prompts() -> list[dict]:
        """获取预设提示词"""
        return [
            {
                "id": "space_cleanup",
                "title": "释放存储空间",
                "prompt": "请分析存储空间使用情况，找出可以安全清理的大文件和冗余内容",
                "description": "找出占用空间大且可安全删除的内容",
                "focus": "all",
            },
            {
                "id": "duplicate_cleanup",
                "title": "清理重复媒体",
                "prompt": "找出重复的媒体文件，保留最高质量版本，建议删除其他版本",
                "description": "识别并清理重复的电影/电视剧文件",
                "focus": "duplicates",
            },
            {
                "id": "quality_upgrade",
                "title": "低质量淘汰",
                "prompt": "找出有高质量版本的媒体中仍保留的低质量版本，建议淘汰",
                "description": "删除 720p 保留 1080p/4K",
                "focus": "low_quality",
            },
            {
                "id": "seeding_complete",
                "title": "已完成保种",
                "prompt": "找出保种任务已完成的下载内容，这些可以安全删除或移动",
                "description": "清理保种已完成的内容",
                "focus": "seeding",
            },
            {
                "id": "old_downloads",
                "title": "旧下载任务",
                "prompt": "找出超过30天的已完成下载任务，分析是否可以清理",
                "description": "清理长期未处理的旧下载",
                "focus": "downloads",
            },
            {
                "id": "conservative",
                "title": "保守清理",
                "prompt": "仅建议最安全的清理操作，只包含保种已完成且确认无用的内容",
                "description": "最小风险的清理建议",
                "focus": "seeding",
            },
        ]
