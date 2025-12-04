"""
AI 阅读助手服务

FUTURE-AI-READING-ASSISTANT-1 P3 实现
提供阅读规划建议的核心业务逻辑
"""

from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai_reading_assistant import ReadingPlanDraft
from app.core.ai_orchestrator.service import AIOrchestratorService, OrchestratorMode
from app.core.ai_orchestrator.tools.base import OrchestratorContext
from app.core.ai_orchestrator.factory import get_llm_client


class AIReadingAssistantService:
    """
    AI 阅读助手服务
    
    提供阅读规划建议功能，调用 Orchestrator READING_ASSISTANT 模式
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_reading_plan(
        self,
        prompt: Optional[str] = None,
        focus: Optional[str] = None,
        goal_type: Optional[str] = None,
        user_id: int = 1,
    ) -> ReadingPlanDraft:
        """
        生成阅读计划草案
        
        Args:
            prompt: 用户自然语言描述（可选）
            focus: 聚焦类型（novel/manga/audiobook/all）
            goal_type: 目标类型（daily/weekly/monthly）
            user_id: 用户 ID
            
        Returns:
            ReadingPlanDraft 阅读计划草案
        """
        try:
            # 构建阅读提示
            reading_prompt = self._build_reading_prompt(prompt, focus, goal_type)
            
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
            
            # 调用 Orchestrator READING_ASSISTANT 模式
            result = await orchestrator.run(
                context=context,
                mode=OrchestratorMode.READING_ASSISTANT,
                prompt=reading_prompt,
            )
            
            # 解析阅读计划草案
            plan = orchestrator.parse_reading_plan(result.llm_suggested_changes)
            
            # 如果解析失败但有 LLM 摘要，补充到草案中
            if not plan.suggestions and result.llm_summary:
                plan.summary = result.llm_summary[:200]
            
            return plan
            
        except Exception as e:
            logger.error(f"[ai_reading_assistant] 生成阅读计划失败: {e}")
            return ReadingPlanDraft.fallback_draft(str(e))
    
    def _build_reading_prompt(
        self,
        user_prompt: Optional[str],
        focus: Optional[str],
        goal_type: Optional[str],
    ) -> str:
        """构建阅读提示"""
        parts = []
        
        # 聚焦类型描述
        if focus:
            focus_desc = {
                "all": "全面分析所有阅读内容",
                "novel": "聚焦于小说阅读",
                "manga": "聚焦于漫画阅读",
                "audiobook": "聚焦于有声书收听",
            }
            parts.append(f"分析范围：{focus_desc.get(focus, '全面分析')}")
        
        # 目标类型
        if goal_type:
            goal_desc = {
                "daily": "设定每日阅读目标",
                "weekly": "设定每周阅读目标",
                "monthly": "设定每月阅读目标",
            }
            parts.append(goal_desc.get(goal_type, ""))
        
        # 用户描述
        if user_prompt:
            parts.append(f"用户需求：{user_prompt}")
        else:
            parts.append("请分析我的阅读进度和书库，给出阅读计划建议。")
        
        return "\n".join(parts)
    
    @staticmethod
    def get_preset_prompts() -> list[dict]:
        """获取预设提示词"""
        return [
            {
                "id": "weekly_plan",
                "title": "本周阅读计划",
                "prompt": "请根据我的阅读进度，制定本周的阅读计划",
                "description": "规划未来一周的阅读目标",
                "focus": "all",
            },
            {
                "id": "finish_ongoing",
                "title": "完成进行中",
                "prompt": "帮我规划如何完成正在阅读的书籍，优先完成进度较高的",
                "description": "专注完成已开始的阅读",
                "focus": "all",
            },
            {
                "id": "novel_focus",
                "title": "小说阅读",
                "prompt": "分析我的小说阅读情况，推荐接下来应该读哪本小说",
                "description": "专注小说类阅读",
                "focus": "novel",
            },
            {
                "id": "manga_focus",
                "title": "漫画阅读",
                "prompt": "分析我的漫画阅读进度，推荐应该继续追哪些漫画",
                "description": "专注漫画类阅读",
                "focus": "manga",
            },
            {
                "id": "series_completion",
                "title": "系列完成",
                "prompt": "帮我找出未完成的系列书籍，优先推荐完成度较高的系列",
                "description": "专注完成系列作品",
                "focus": "all",
            },
            {
                "id": "new_start",
                "title": "开始新书",
                "prompt": "我想开始读新书，根据我的阅读历史推荐适合我的待读书籍",
                "description": "从待读书单中选择",
                "focus": "all",
            },
        ]
