"""
AI Orchestrator 核心服务

FUTURE-AI-ORCHESTRATOR-1 P3 实现
FUTURE-AI-SUBS-WORKFLOW-1 P2 增强

编排 LLM 与本地 AI 器官的交互，实现只读版 AI 总控
"""

import json
import re
from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger

from .llm_client import LLMClient, ChatMessage, MessageRole, LLMToolCall, LLMResponse
from .tools.base import AITool, OrchestratorContext
from .tools.registry import get_tool_registry


class OrchestratorMode(str, Enum):
    """Orchestrator 运行模式"""
    GENERIC = "generic"
    SUBS_ADVISOR = "subs_advisor"
    DIAGNOSE = "diagnose"
    CLEANUP_ADVISOR = "cleanup_advisor"


class PlannedToolCall(BaseModel):
    """计划的工具调用"""
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    status: str = "pending"  # pending / success / failed / skipped
    error: Optional[str] = None


class OrchestratorResult(BaseModel):
    """Orchestrator 执行结果"""
    plan: list[PlannedToolCall] = Field(default_factory=list)
    tool_results: dict[str, Any] = Field(default_factory=dict)
    llm_summary: str = ""
    llm_suggested_changes: Optional[dict] = None
    mode: str = ""
    error: Optional[str] = None


# 模式与允许工具的映射
MODE_ALLOWED_TOOLS: dict[OrchestratorMode, list[str]] = {
    OrchestratorMode.SUBS_ADVISOR: [
        "get_site_and_sub_overview",
        "get_search_preview",
        "get_torrent_index_insight",
        "get_recommendation_preview",
    ],
    OrchestratorMode.DIAGNOSE: [
        "get_health_status",
        "get_log_snapshot",
        "get_site_and_sub_overview",
        "get_runner_status",  # FUTURE-AI-LOG-DOCTOR-1
    ],
    OrchestratorMode.CLEANUP_ADVISOR: [
        "get_torrent_index_insight",
        "get_storage_snapshot",  # FUTURE-AI-CLEANUP-ADVISOR-1
        "get_library_snapshot",  # FUTURE-AI-CLEANUP-ADVISOR-1
        "get_site_and_sub_overview",
    ],
    OrchestratorMode.READING_ASSISTANT: [
        "get_reading_snapshot",  # FUTURE-AI-READING-ASSISTANT-1
        "get_library_books",  # FUTURE-AI-READING-ASSISTANT-1
        "get_recommendation_preview",
    ],
    OrchestratorMode.GENERIC: [
        "get_site_and_sub_overview",
        "get_health_status",
    ],
}

# 单次会话最大工具调用次数
MAX_TOOL_CALLS = 3


class AIOrchestratorService:
    """
    AI Orchestrator 核心服务
    
    编排 LLM 与本地 AI 器官的交互
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.registry = get_tool_registry()
    
    async def run(
        self,
        context: OrchestratorContext,
        mode: OrchestratorMode,
        prompt: str,
    ) -> OrchestratorResult:
        """
        执行 Orchestrator 流程
        
        Args:
            context: 执行上下文
            mode: 运行模式
            prompt: 用户输入的自然语言请求
            
        Returns:
            执行结果
        """
        result = OrchestratorResult(mode=mode.value)
        
        try:
            # 1. 获取允许的工具集
            allowed_tools = self._get_allowed_tools(mode)
            tool_specs = self.registry.get_llm_tool_specs(allowed_tools)
            
            if not tool_specs:
                result.llm_summary = "当前模式下没有可用的工具。"
                return result
            
            # 2. 构造系统提示
            system_prompt = self._build_system_prompt(mode, allowed_tools)
            
            # 3. 第一次 LLM 调用：获取工具调用计划
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=MessageRole.USER, content=prompt),
            ]
            
            llm_response = await self.llm_client.chat(messages, tools=tool_specs)
            
            # 4. 处理工具调用
            if llm_response.tool_calls:
                result.plan = self._parse_tool_calls(llm_response.tool_calls, allowed_tools)
                
                # 执行工具
                result.tool_results = await self._execute_tools(result.plan, context)
                
                # 5. 第二次 LLM 调用：生成总结
                result.llm_summary, result.llm_suggested_changes = await self._generate_summary(
                    messages=messages,
                    tool_results=result.tool_results,
                    mode=mode,
                )
            else:
                # LLM 直接返回文本响应
                result.llm_summary = llm_response.content or "无法理解您的请求，请尝试更具体的描述。"
            
            # 记录调试日志
            self._log_execution(result, context.debug_mode)
            
        except Exception as e:
            logger.error(f"[orchestrator] 执行失败: {e}")
            result.error = str(e)[:200]
            result.llm_summary = f"执行过程中发生错误: {str(e)[:100]}"
        
        return result
    
    async def plan_only(
        self,
        context: OrchestratorContext,
        mode: OrchestratorMode,
        prompt: str,
    ) -> OrchestratorResult:
        """
        仅生成执行计划，不实际执行工具
        
        Args:
            context: 执行上下文
            mode: 运行模式
            prompt: 用户输入
            
        Returns:
            包含计划但无工具结果的结果
        """
        result = OrchestratorResult(mode=mode.value)
        
        try:
            allowed_tools = self._get_allowed_tools(mode)
            tool_specs = self.registry.get_llm_tool_specs(allowed_tools)
            
            if not tool_specs:
                result.llm_summary = "当前模式下没有可用的工具。"
                return result
            
            system_prompt = self._build_system_prompt(mode, allowed_tools)
            
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=MessageRole.USER, content=prompt),
            ]
            
            llm_response = await self.llm_client.chat(messages, tools=tool_specs)
            
            if llm_response.tool_calls:
                result.plan = self._parse_tool_calls(llm_response.tool_calls, allowed_tools)
                result.llm_summary = f"计划调用 {len(result.plan)} 个工具：" + ", ".join(
                    p.tool_name for p in result.plan
                )
            else:
                result.llm_summary = llm_response.content or "无需调用工具。"
            
        except Exception as e:
            logger.error(f"[orchestrator] 计划生成失败: {e}")
            result.error = str(e)[:200]
        
        return result
    
    def _get_allowed_tools(self, mode: OrchestratorMode) -> list[str]:
        """获取模式允许的工具列表"""
        return MODE_ALLOWED_TOOLS.get(mode, MODE_ALLOWED_TOOLS[OrchestratorMode.GENERIC])
    
    def _build_system_prompt(self, mode: OrchestratorMode, allowed_tools: list[str]) -> str:
        """构建系统提示"""
        # SUBS_ADVISOR 模式使用专用的详细提示
        if mode == OrchestratorMode.SUBS_ADVISOR:
            return self._build_subs_advisor_prompt(allowed_tools)
        
        # DIAGNOSE 模式使用专用的诊断提示
        if mode == OrchestratorMode.DIAGNOSE:
            return self._build_diagnose_prompt(allowed_tools)
        
        # CLEANUP_ADVISOR 模式使用专用的清理提示
        if mode == OrchestratorMode.CLEANUP_ADVISOR:
            return self._build_cleanup_advisor_prompt(allowed_tools)
        
        # READING_ASSISTANT 模式使用专用的阅读提示
        if mode == OrchestratorMode.READING_ASSISTANT:
            return self._build_reading_assistant_prompt(allowed_tools)
        
        mode_descriptions = {
            OrchestratorMode.SUBS_ADVISOR: (
                "你是 VabHub 的订阅工作流顾问。"
                "帮助用户分析站点配置、订阅规则和 RSSHub 源，提供优化建议。"
            ),
            OrchestratorMode.DIAGNOSE: (
                "你是 VabHub 的系统诊断助手。"
                "帮助用户排查系统问题，分析健康状态和日志，找出潜在故障。"
            ),
            OrchestratorMode.CLEANUP_ADVISOR: (
                "你是 VabHub 的整理优化顾问。"
                "帮助用户分析 HR 风险、推荐内容整理策略，优化存储空间。"
            ),
            OrchestratorMode.GENERIC: (
                "你是 VabHub 的 AI 助手。"
                "帮助用户了解系统状态和配置信息。"
            ),
        }
        
        return f"""
{mode_descriptions.get(mode, mode_descriptions[OrchestratorMode.GENERIC])}

重要限制：
1. 你只能使用以下工具：{', '.join(allowed_tools)}
2. 你不能修改任何配置或执行任何写操作
3. 所有建议都应该是"草案"形式，由用户决定是否采纳
4. 不要访问或输出敏感信息（密码、Cookie、Token 等）

如果需要提供配置建议，请使用 JSON 格式输出，并明确标注为"建议配置（草案）"。
""".strip()
    
    def _parse_tool_calls(
        self,
        tool_calls: list[LLMToolCall],
        allowed_tools: list[str],
    ) -> list[PlannedToolCall]:
        """解析并过滤工具调用"""
        parsed: list[PlannedToolCall] = []
        
        for tc in tool_calls[:MAX_TOOL_CALLS]:  # 限制数量
            # 检查工具是否允许
            if tc.name not in allowed_tools:
                logger.warning(f"[orchestrator] 工具 {tc.name} 不在允许列表中，跳过")
                parsed.append(PlannedToolCall(
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    status="skipped",
                    error="工具不在允许列表中",
                ))
                continue
            
            # 检查工具是否注册
            if tc.name not in self.registry:
                logger.warning(f"[orchestrator] 工具 {tc.name} 未注册，跳过")
                parsed.append(PlannedToolCall(
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    status="skipped",
                    error="工具未注册",
                ))
                continue
            
            parsed.append(PlannedToolCall(
                tool_name=tc.name,
                arguments=tc.arguments,
                status="pending",
            ))
        
        return parsed
    
    async def _execute_tools(
        self,
        plan: list[PlannedToolCall],
        context: OrchestratorContext,
    ) -> dict[str, Any]:
        """执行工具调用"""
        results: dict[str, Any] = {}
        
        for planned in plan:
            if planned.status != "pending":
                continue
            
            tool = self.registry.get(planned.tool_name)
            if not tool:
                planned.status = "failed"
                planned.error = "工具不存在"
                continue
            
            try:
                # 解析参数
                params = tool.input_model(**planned.arguments)
                
                # 执行工具
                output = await tool.run(params, context)
                
                # 记录结果
                results[planned.tool_name] = output.model_dump()
                planned.status = "success"
                
            except Exception as e:
                logger.error(f"[orchestrator] 工具 {planned.tool_name} 执行失败: {e}")
                planned.status = "failed"
                planned.error = str(e)[:100]
                results[planned.tool_name] = {"error": str(e)[:100]}
        
        return results
    
    async def _generate_summary(
        self,
        messages: list[ChatMessage],
        tool_results: dict[str, Any],
        mode: OrchestratorMode,
    ) -> tuple[str, Optional[dict]]:
        """生成总结和建议"""
        # 构造工具结果消息
        tool_results_text = "工具执行结果：\n"
        for tool_name, result in tool_results.items():
            # 提取摘要文本
            summary = result.get("summary_text", str(result)[:500])
            tool_results_text += f"\n### {tool_name}\n{summary}\n"
        
        # 添加工具结果到消息
        messages.append(ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"已执行工具，以下是结果：\n{tool_results_text}",
        ))
        
        # 请求总结
        summary_prompt = """
基于以上工具执行结果，请：
1. 用简洁的中文总结分析结果（不超过 200 字）
2. 如果有具体的优化建议，请以 JSON 格式输出（可选）

格式示例：
总结：[你的总结]

建议配置（草案）：
```json
{
  "建议类型": "...",
  "建议内容": "..."
}
```
"""
        messages.append(ChatMessage(role=MessageRole.USER, content=summary_prompt))
        
        # 调用 LLM
        response = await self.llm_client.chat(messages)
        
        # 解析响应
        content = response.content or ""
        summary = content
        suggested_changes: Optional[dict] = None
        
        # 尝试提取 JSON 建议
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                import json
                suggested_changes = json.loads(json_match.group(1))
                # 从摘要中移除 JSON 部分
                summary = content[:json_match.start()].strip()
            except json.JSONDecodeError:
                pass
        
        return summary, suggested_changes
    
    def _build_subs_advisor_prompt(self, allowed_tools: list[str]) -> str:
        """
        构建 SUBS_ADVISOR 模式的专用系统提示
        
        FUTURE-AI-SUBS-WORKFLOW-1 P2 实现
        指导 LLM 生成符合 SubsWorkflowDraft schema 的订阅草案
        """
        return f"""你是 VabHub 的 AI 订阅工作流顾问。

你的任务是帮助用户创建订阅规则草案。根据用户的自然语言请求，你需要：
1. 调用工具获取站点、RSSHub 源、搜索预览等信息
2. 基于工具返回的数据，生成订阅工作流草案
3. 草案必须以特定 JSON 格式输出

可用工具：{', '.join(allowed_tools)}

【重要约束】
- 你只能生成"草案"，不能直接创建订阅
- 最多生成 3 个草案
- 所有源/站点/分辨率应基于工具返回的实际数据，不要凭空臆造
- 输出 JSON 必须严格符合以下 schema

【输出 JSON Schema】
```json
{{
  "drafts": [
    {{
      "name": "订阅名称",
      "description": "订阅描述（可选）",
      "media_type": "movie | tv | anime",
      "sources": [
        {{
          "type": "rsshub | pt_search",
          "id": "源ID（RSSHub source_id 或站点 key）",
          "name": "源名称"
        }}
      ],
      "filter_rule": {{
        "include_keywords": ["关键词1", "关键词2"],
        "exclude_keywords": ["排除词"],
        "min_resolution": "1080p | 2160p",
        "hr_safe": true,
        "languages": ["中文", "韩语"]
      }},
      "action": {{
        "download_enabled": false,
        "dry_run": true,
        "notify_on_match": true
      }},
      "ai_explanation": "对该草案的解释说明"
    }}
  ],
  "summary": "总体说明",
  "notes": "风险提示或注意事项（可选）"
}}
```

【字段说明】
- media_type: 必须是 movie / tv / anime 之一
- sources.type: rsshub 表示 RSSHub 源，pt_search 表示 PT 站点搜索
- sources.id: 必须是工具返回的有效 ID
- hr_safe: true 表示优先安全（不下载 HR 种），false 表示允许 HR
- download_enabled: v1 版本建议设为 false，让用户手动启用

请先调用工具获取信息，然后基于结果生成草案 JSON。
"""
    
    def parse_subs_advisor_drafts(self, llm_suggested_changes: Optional[dict]) -> tuple[list[dict], str, Optional[str]]:
        """
        从 LLM 建议中解析订阅草案
        
        FUTURE-AI-SUBS-WORKFLOW-1 P2 实现
        
        Args:
            llm_suggested_changes: LLM 返回的建议 JSON
            
        Returns:
            (drafts, summary, notes) 三元组
        """
        if not llm_suggested_changes:
            return [], "", None
        
        drafts = []
        summary = ""
        notes = None
        
        # 尝试提取 drafts 数组
        if isinstance(llm_suggested_changes, dict):
            raw_drafts = llm_suggested_changes.get("drafts", [])
            summary = llm_suggested_changes.get("summary", "")
            notes = llm_suggested_changes.get("notes")
            
            # 验证和转换每个草案
            for raw in raw_drafts:
                if not isinstance(raw, dict):
                    continue
                
                # 基本验证
                if not raw.get("name") or not raw.get("media_type"):
                    logger.warning(f"[orchestrator] 草案缺少必要字段: {raw}")
                    continue
                
                # 验证 media_type
                media_type = raw.get("media_type", "").lower()
                if media_type not in ("movie", "tv", "anime", "short_drama", "music", "book", "comic"):
                    logger.warning(f"[orchestrator] 无效的 media_type: {media_type}")
                    continue
                
                drafts.append(raw)
        
        # 限制最多 3 个草案
        return drafts[:3], summary, notes
    
    def _build_diagnose_prompt(self, allowed_tools: list[str]) -> str:
        """
        构建 DIAGNOSE 模式的专用系统提示
        
        FUTURE-AI-LOG-DOCTOR-1 P2 实现
        指导 LLM 生成符合 SystemDiagnosisReport schema 的诊断报告
        """
        return f"""你是 VabHub 系统的 AI 故障医生。

你的任务是分析系统健康状况并生成诊断报告。根据用户描述的问题或诊断请求，你需要：
1. 调用工具获取系统健康状态、日志快照、Runner 状态、站点状态等信息
2. 分析这些数据，找出问题和潜在风险
3. 生成结构化的诊断报告 JSON

可用工具：{', '.join(allowed_tools)}

【重要约束】
- 你只是在提供诊断和建议，不会自动执行任何修复操作
- 建议步骤应该是人类可以执行的具体操作
- 对于需要修改配置或重启服务的步骤，明确标注 is_safe=false
- 不要输出敏感信息（密码、Cookie、Token 等）

【输出 JSON Schema】
```json
{{
  "overall_status": "info | warning | error | critical",
  "summary": "一句话总结当前系统状态",
  "items": [
    {{
      "id": "唯一标识",
      "severity": "info | warning | error | critical",
      "title": "问题标题",
      "description": "问题详细描述",
      "evidence": ["支持该诊断的证据1", "证据2"],
      "related_components": ["组件标识1", "组件2"]
    }}
  ],
  "suggested_steps": [
    {{
      "step": 1,
      "title": "步骤标题",
      "detail": "详细操作说明",
      "is_safe": true
    }}
  ]
}}
```

【字段说明】
- overall_status: 总体健康评分，根据最严重的问题决定
- items: 诊断项列表，按严重程度排序（critical > error > warning > info）
- items[].evidence: 支持该诊断的证据，如日志片段、检查结果摘要
- items[].related_components: 相关组件，如 ["database", "rsshub", "site:xxxxx"]
- suggested_steps: 建议的操作步骤，按顺序编号
- suggested_steps[].is_safe: true 表示只读检查，false 表示需要修改配置/重启服务

【严重程度判定】
- critical: 系统核心组件不可用（数据库宕机、磁盘空间耗尽）
- error: 重要功能受损（下载器连接失败、关键 Runner 持续失败）
- warning: 存在隐患但暂不影响使用（磁盘空间紧张、偶发错误）
- info: 仅供参考的信息（正常运行状态、统计数据）

请先调用工具获取系统状态信息，然后基于结果生成诊断报告 JSON。
"""
    
    def parse_diagnosis_report(self, llm_suggested_changes: Optional[dict]) -> "SystemDiagnosisReport":
        """
        从 LLM 建议中解析诊断报告
        
        FUTURE-AI-LOG-DOCTOR-1 P2 实现
        
        Args:
            llm_suggested_changes: LLM 返回的建议 JSON
            
        Returns:
            SystemDiagnosisReport 实例
        """
        from app.schemas.ai_log_doctor import (
            SystemDiagnosisReport,
            DiagnosisItem,
            DiagnosisPlanStep,
            DiagnosisSeverity,
        )
        from datetime import datetime
        
        if not llm_suggested_changes:
            return SystemDiagnosisReport.fallback_report("LLM 未返回诊断数据")
        
        try:
            # 解析 overall_status
            raw_status = llm_suggested_changes.get("overall_status", "info")
            try:
                overall_status = DiagnosisSeverity(raw_status.lower())
            except ValueError:
                overall_status = DiagnosisSeverity.INFO
            
            # 解析 summary
            summary = llm_suggested_changes.get("summary", "")
            
            # 解析 items
            items: list[DiagnosisItem] = []
            raw_items = llm_suggested_changes.get("items", [])
            for i, raw_item in enumerate(raw_items[:20]):  # 限制最多 20 项
                if not isinstance(raw_item, dict):
                    continue
                
                try:
                    item_severity = DiagnosisSeverity(
                        raw_item.get("severity", "info").lower()
                    )
                except ValueError:
                    item_severity = DiagnosisSeverity.INFO
                
                items.append(DiagnosisItem(
                    id=raw_item.get("id", f"item_{i}"),
                    severity=item_severity,
                    title=raw_item.get("title", "未知问题")[:100],
                    description=raw_item.get("description", "")[:500],
                    evidence=raw_item.get("evidence", [])[:5],
                    related_components=raw_item.get("related_components", [])[:10],
                ))
            
            # 解析 suggested_steps
            steps: list[DiagnosisPlanStep] = []
            raw_steps = llm_suggested_changes.get("suggested_steps", [])
            for j, raw_step in enumerate(raw_steps[:10]):  # 限制最多 10 步
                if not isinstance(raw_step, dict):
                    continue
                
                steps.append(DiagnosisPlanStep(
                    step=raw_step.get("step", j + 1),
                    title=raw_step.get("title", f"步骤 {j + 1}")[:100],
                    detail=raw_step.get("detail", "")[:500],
                    is_safe=raw_step.get("is_safe", True),
                ))
            
            return SystemDiagnosisReport(
                overall_status=overall_status,
                summary=summary[:200],
                items=items,
                suggested_steps=steps,
                raw_refs={"original": llm_suggested_changes},
                generated_at=datetime.now().isoformat(),
            )
            
        except Exception as e:
            logger.error(f"[orchestrator] 解析诊断报告失败: {e}")
            report = SystemDiagnosisReport.fallback_report(str(e))
            report.raw_refs = {"original": llm_suggested_changes, "error": str(e)}
            return report
    
    def _build_cleanup_advisor_prompt(self, allowed_tools: list[str]) -> str:
        """
        构建 CLEANUP_ADVISOR 模式的专用系统提示
        
        FUTURE-AI-CLEANUP-ADVISOR-1 P2 实现
        指导 LLM 生成符合 CleanupPlanDraft schema 的清理计划草案
        """
        return f"""你是 VabHub 的 AI 整理顾问。

你的任务是分析用户的存储使用情况、媒体库内容和保种任务，生成清理计划草案。

你会收到：
1. 存储空间使用情况和趋势
2. 媒体库统计（按类型、质量分组）
3. HR/保种任务状态
4. 重复媒体和清理候选

可用工具：{', '.join(allowed_tools)}

【重要约束】
- 你只是在生成"草案"，不会自动执行任何删除或移动操作
- 对于仍在保种中的内容（hr_status=active），必须标注 risk_level=risky
- 不要建议删除唯一版本的媒体（除非用户明确要求）
- 建议按 risk_level 排序，safe 在前，risky 在后

【输出 JSON Schema】
```json
{{
  "summary": "总体说明",
  "total_savable_gb": 100.5,
  "actions": [
    {{
      "id": "唯一标识",
      "action_type": "delete | archive | transcode | replace",
      "target_type": "media_file | download_task | torrent",
      "target_id": "目标ID",
      "target_title": "目标标题",
      "target_path": "文件路径（可选）",
      "size_gb": 10.5,
      "reason": "建议原因",
      "risk_level": "safe | caution | risky",
      "risk_notes": ["风险提示1", "风险提示2"],
      "hr_status": "active | completed | none"
    }}
  ],
  "storage_context": {{
    "total_space_gb": 1000,
    "used_gb": 800,
    "free_gb": 200
  }},
  "warnings": ["全局警告1"]
}}
```

【字段说明】
- action_type: 操作类型
  - delete: 删除文件
  - archive: 归档到冷存储
  - transcode: 转码压缩（减小体积）
  - replace: 质量替换（删除低质量版本）
- risk_level: 风险级别
  - safe: 安全操作（保种已完成、重复低质量版本）
  - caution: 需谨慎（可能仍有价值）
  - risky: 高风险（仍在保种中，不建议操作）
- hr_status: 保种状态
  - active: 仍在保种中
  - completed: 保种任务已完成
  - none: 无保种记录

请先调用工具获取存储和媒体库信息，然后基于结果生成清理计划草案 JSON。
"""
    
    def parse_cleanup_draft(self, llm_suggested_changes: Optional[dict]) -> "CleanupPlanDraft":
        """
        从 LLM 建议中解析清理计划草案
        
        FUTURE-AI-CLEANUP-ADVISOR-1 P2 实现
        
        Args:
            llm_suggested_changes: LLM 返回的建议 JSON
            
        Returns:
            CleanupPlanDraft 实例
        """
        from app.schemas.ai_cleanup_advisor import (
            CleanupPlanDraft,
            CleanupAction,
            CleanupActionType,
            RiskLevel,
        )
        from datetime import datetime
        
        if not llm_suggested_changes:
            return CleanupPlanDraft.fallback_draft("LLM 未返回清理计划数据")
        
        try:
            # 解析 summary
            summary = llm_suggested_changes.get("summary", "")
            
            # 解析 total_savable_gb
            total_savable = llm_suggested_changes.get("total_savable_gb", 0.0)
            
            # 解析 actions
            actions: list[CleanupAction] = []
            raw_actions = llm_suggested_changes.get("actions", [])
            for i, raw in enumerate(raw_actions[:50]):  # 限制最多 50 项
                if not isinstance(raw, dict):
                    continue
                
                # 解析 action_type
                try:
                    action_type = CleanupActionType(raw.get("action_type", "delete").lower())
                except ValueError:
                    action_type = CleanupActionType.DELETE
                
                # 解析 risk_level
                try:
                    risk_level = RiskLevel(raw.get("risk_level", "caution").lower())
                except ValueError:
                    risk_level = RiskLevel.CAUTION
                
                actions.append(CleanupAction(
                    id=raw.get("id", f"action_{i}"),
                    action_type=action_type,
                    target_type=raw.get("target_type", "download_task"),
                    target_id=str(raw.get("target_id", "")),
                    target_title=raw.get("target_title", "未知")[:100],
                    target_path=raw.get("target_path"),
                    size_gb=float(raw.get("size_gb", 0)),
                    reason=raw.get("reason", "")[:200],
                    risk_level=risk_level,
                    risk_notes=raw.get("risk_notes", [])[:5],
                    hr_status=raw.get("hr_status"),
                ))
            
            # 解析 warnings
            warnings = llm_suggested_changes.get("warnings", [])[:10]
            
            # 解析 storage_context
            storage_context = llm_suggested_changes.get("storage_context", {})
            
            return CleanupPlanDraft(
                summary=summary[:200],
                total_savable_gb=round(total_savable, 2),
                actions=actions,
                storage_context=storage_context,
                warnings=warnings,
                generated_at=datetime.now().isoformat(),
            )
            
        except Exception as e:
            logger.error(f"[orchestrator] 解析清理计划草案失败: {e}")
            draft = CleanupPlanDraft.fallback_draft(str(e))
            return draft
    
    def _build_reading_assistant_prompt(self, allowed_tools: list[str]) -> str:
        """
        构建 READING_ASSISTANT 模式的专用系统提示
        
        FUTURE-AI-READING-ASSISTANT-1 P2 实现
        指导 LLM 生成符合 ReadingPlanDraft schema 的阅读计划草案
        """
        return f"""你是 VabHub 的 AI 阅读助手。

你的任务是分析用户的阅读进度、书库存量和阅读习惯，生成个性化的阅读计划建议。

你会收到：
1. 用户阅读进度（正在阅读、已完成、待读）
2. 书库统计（按类型、系列分组）
3. 最近阅读活动

可用工具：{', '.join(allowed_tools)}

【重要约束】
- 你只是在生成"规划建议"，不会修改任何阅读进度
- 建议应该具体且可执行
- 考虑用户的阅读节奏，不要给出过于激进的目标
- 优先建议完成进行中的阅读，再开始新书

【输出 JSON Schema】
```json
{{
  "summary": "总体说明",
  "goals": [
    {{
      "goal_type": "weekly | monthly",
      "target_count": 2,
      "current_count": 0,
      "media_types": ["novel", "manga"],
      "description": "目标描述"
    }}
  ],
  "suggestions": [
    {{
      "suggestion_type": "continue | start | finish",
      "media_type": "novel | manga | audiobook",
      "item_id": 123,
      "title": "书名",
      "author": "作者",
      "reason": "推荐理由",
      "priority": "high | medium | low",
      "estimated_time": "预估阅读时间",
      "current_progress": "当前进度"
    }}
  ],
  "stats_context": {{
    "ongoing_count": 5,
    "finished_count": 10,
    "unread_count": 20
  }},
  "insights": ["阅读洞察1", "阅读洞察2"]
}}
```

【字段说明】
- suggestion_type: 建议类型
  - continue: 继续阅读（已开始未完成）
  - start: 开始新书（未阅读）
  - finish: 完成当前（快完成的书）
- priority: 优先级
  - high: 高优先级（快完成的或重要的）
  - medium: 中优先级
  - low: 低优先级

请先调用工具获取阅读进度和书库信息，然后基于结果生成阅读计划草案 JSON。
"""
    
    def parse_reading_plan(self, llm_suggested_changes: Optional[dict]) -> "ReadingPlanDraft":
        """
        从 LLM 建议中解析阅读计划草案
        
        FUTURE-AI-READING-ASSISTANT-1 P2 实现
        
        Args:
            llm_suggested_changes: LLM 返回的建议 JSON
            
        Returns:
            ReadingPlanDraft 实例
        """
        from app.schemas.ai_reading_assistant import (
            ReadingPlanDraft,
            ReadingGoal,
            ReadingGoalType,
            ReadingSuggestion,
            SuggestionType,
            SuggestionPriority,
        )
        from datetime import datetime
        
        if not llm_suggested_changes:
            return ReadingPlanDraft.fallback_draft("LLM 未返回阅读计划数据")
        
        try:
            # 解析 summary
            summary = llm_suggested_changes.get("summary", "")
            
            # 解析 goals
            goals: list[ReadingGoal] = []
            raw_goals = llm_suggested_changes.get("goals", [])
            for raw in raw_goals[:10]:
                if not isinstance(raw, dict):
                    continue
                
                try:
                    goal_type = ReadingGoalType(raw.get("goal_type", "weekly").lower())
                except ValueError:
                    goal_type = ReadingGoalType.WEEKLY
                
                goals.append(ReadingGoal(
                    goal_type=goal_type,
                    target_count=int(raw.get("target_count", 1)),
                    current_count=int(raw.get("current_count", 0)),
                    media_types=raw.get("media_types", []),
                    deadline=raw.get("deadline"),
                    description=raw.get("description", "")[:100],
                ))
            
            # 解析 suggestions
            suggestions: list[ReadingSuggestion] = []
            raw_suggestions = llm_suggested_changes.get("suggestions", [])
            for raw in raw_suggestions[:20]:
                if not isinstance(raw, dict):
                    continue
                
                try:
                    suggestion_type = SuggestionType(raw.get("suggestion_type", "continue").lower())
                except ValueError:
                    suggestion_type = SuggestionType.CONTINUE
                
                try:
                    priority = SuggestionPriority(raw.get("priority", "medium").lower())
                except ValueError:
                    priority = SuggestionPriority.MEDIUM
                
                suggestions.append(ReadingSuggestion(
                    suggestion_type=suggestion_type,
                    media_type=raw.get("media_type", "novel"),
                    item_id=raw.get("item_id"),
                    title=raw.get("title", "未知")[:100],
                    author=raw.get("author"),
                    reason=raw.get("reason", "")[:200],
                    priority=priority,
                    estimated_time=raw.get("estimated_time"),
                    current_progress=raw.get("current_progress"),
                ))
            
            # 解析 insights
            insights = llm_suggested_changes.get("insights", [])[:10]
            
            # 解析 stats_context
            stats_context = llm_suggested_changes.get("stats_context", {})
            
            return ReadingPlanDraft(
                summary=summary[:200],
                goals=goals,
                suggestions=suggestions,
                stats_context=stats_context,
                insights=insights,
                generated_at=datetime.now().isoformat(),
            )
            
        except Exception as e:
            logger.error(f"[orchestrator] 解析阅读计划草案失败: {e}")
            return ReadingPlanDraft.fallback_draft(str(e))
    
    def _log_execution(self, result: OrchestratorResult, debug: bool) -> None:
        """记录执行日志"""
        from app.core.config import settings
        
        if not (debug or settings.AI_ORCH_DEBUG_LOG):
            return
        
        logger.info(
            f"[orchestrator] 执行完成 | "
            f"mode={result.mode} | "
            f"tools={len(result.plan)} | "
            f"success={sum(1 for p in result.plan if p.status == 'success')} | "
            f"has_suggestions={result.llm_suggested_changes is not None}"
        )
