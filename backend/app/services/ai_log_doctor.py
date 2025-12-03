"""
AI 故障医生服务

FUTURE-AI-LOG-DOCTOR-1 P3 实现
提供系统健康诊断的核心业务逻辑
"""

from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai_log_doctor import (
    SystemDiagnosisReport,
    DiagnosisScope,
    DiagnosisTimeWindow,
    DiagnosisFocus,
    DiagnosisSeverity,
    DiagnosisItem,
    DiagnosisPlanStep,
)
from app.core.ai_orchestrator.service import AIOrchestratorService, OrchestratorMode
from app.core.ai_orchestrator.tools.base import OrchestratorContext
from app.core.ai_orchestrator.llm_client import get_llm_client


class AILogDoctorService:
    """
    AI 故障医生服务
    
    提供系统健康诊断功能，调用 Orchestrator DIAGNOSE 模式
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def diagnose_system(
        self,
        prompt: Optional[str] = None,
        scope: Optional[DiagnosisScope] = None,
        user_id: int = 1,
    ) -> SystemDiagnosisReport:
        """
        执行系统诊断
        
        Args:
            prompt: 用户自然语言描述（可选）
            scope: 诊断范围配置
            user_id: 用户 ID
            
        Returns:
            SystemDiagnosisReport 诊断报告
        """
        try:
            # 构建诊断提示
            diagnosis_prompt = self._build_diagnosis_prompt(prompt, scope)
            
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
            
            # 调用 Orchestrator DIAGNOSE 模式
            result = await orchestrator.run(
                context=context,
                mode=OrchestratorMode.DIAGNOSE,
                prompt=diagnosis_prompt,
            )
            
            # 解析诊断报告
            report = orchestrator.parse_diagnosis_report(result.llm_suggested_changes)
            
            # 如果解析失败但有 LLM 摘要，补充到报告中
            if not report.items and result.llm_summary:
                report.summary = result.llm_summary[:200]
            
            # 添加工具执行结果到 raw_refs
            if result.tool_results:
                report.raw_refs["tool_results"] = result.tool_results
            
            # 添加执行计划到 raw_refs
            if result.plan:
                report.raw_refs["plan"] = [
                    {
                        "tool": p.tool_name,
                        "status": p.status,
                        "error": p.error,
                    }
                    for p in result.plan
                ]
            
            return report
            
        except Exception as e:
            logger.error(f"[ai_log_doctor] 诊断失败: {e}")
            return SystemDiagnosisReport.fallback_report(str(e))
    
    def _build_diagnosis_prompt(
        self,
        user_prompt: Optional[str],
        scope: Optional[DiagnosisScope],
    ) -> str:
        """构建诊断提示"""
        parts = []
        
        # 时间窗口描述
        if scope:
            time_desc = {
                DiagnosisTimeWindow.HOUR_1: "最近 1 小时",
                DiagnosisTimeWindow.HOUR_24: "最近 24 小时",
                DiagnosisTimeWindow.DAY_7: "最近 7 天",
            }
            parts.append(f"时间范围：{time_desc.get(scope.time_window, '最近 24 小时')}")
            
            # 聚焦组件描述
            focus_desc = {
                DiagnosisFocus.ALL: "全面检查",
                DiagnosisFocus.DOWNLOAD: "下载相关（下载器、下载任务）",
                DiagnosisFocus.RSSHUB: "RSSHub 订阅相关",
                DiagnosisFocus.SITE: "站点连通性",
                DiagnosisFocus.RUNNER: "定时任务/Runner",
                DiagnosisFocus.TELEGRAM: "Telegram Bot 相关",
                DiagnosisFocus.STORAGE: "存储空间相关",
            }
            if scope.focus != DiagnosisFocus.ALL:
                parts.append(f"聚焦检查：{focus_desc.get(scope.focus, '全面检查')}")
        
        # 用户描述
        if user_prompt:
            parts.append(f"用户描述的问题：{user_prompt}")
        else:
            parts.append("请进行全面的系统健康检查，找出潜在问题并给出建议。")
        
        return "\n".join(parts)
    
    @staticmethod
    def get_preset_prompts() -> list[dict]:
        """获取预设提示词"""
        return [
            {
                "id": "full_check_24h",
                "title": "24 小时全面体检",
                "prompt": "对系统进行全面的健康检查，包括数据库、下载器、站点、定时任务等所有组件",
                "description": "检查最近 24 小时内的系统健康状况",
                "focus": None,
            },
            {
                "id": "download_issues",
                "title": "下载问题排查",
                "prompt": "最近下载经常失败，请帮我检查下载器连接、站点状态和相关日志",
                "description": "排查下载失败的原因",
                "focus": "download",
            },
            {
                "id": "rsshub_issues",
                "title": "RSSHub 订阅问题",
                "prompt": "RSSHub 订阅好像不更新了，请检查相关服务和任务状态",
                "description": "排查 RSSHub 订阅不更新的原因",
                "focus": "rsshub",
            },
            {
                "id": "site_connectivity",
                "title": "站点连通性检查",
                "prompt": "请检查所有站点的连通性和访问状态",
                "description": "检查 PT 站点是否可正常访问",
                "focus": "site",
            },
            {
                "id": "runner_status",
                "title": "定时任务状态",
                "prompt": "请检查所有定时任务的运行状态，找出失败或异常的任务",
                "description": "检查订阅刷新、签到等定时任务",
                "focus": "runner",
            },
            {
                "id": "storage_check",
                "title": "存储空间检查",
                "prompt": "请检查磁盘空间使用情况，看是否有空间不足的风险",
                "description": "检查存储空间和使用趋势",
                "focus": "storage",
            },
            {
                "id": "error_analysis",
                "title": "错误日志分析",
                "prompt": "请分析最近的错误日志，找出频繁出现的问题和可能的原因",
                "description": "分析 ERROR 级别日志",
                "focus": None,
            },
        ]
