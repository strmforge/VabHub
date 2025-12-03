/**
 * AI Orchestrator API
 * 
 * FUTURE-AI-ORCHESTRATOR-1 P5 实现
 * 提供 AI 总控层的前端 API 调用
 */

import axios from 'axios'

const API_BASE = '/api/ai/orchestrator'

// 类型定义
export interface OrchestratorStatus {
  enabled: boolean
  llm_configured: boolean
  available_tools: string[]
  modes: string[]
}

export interface ToolInfo {
  name: string
  description: string
}

export interface PlannedToolCall {
  tool_name: string
  arguments: Record<string, any>
  status: 'pending' | 'success' | 'failed' | 'skipped'
  error?: string
}

export interface OrchestratorResult {
  plan: PlannedToolCall[]
  tool_results: Record<string, any>
  llm_summary: string
  llm_suggested_changes?: Record<string, any>
  mode: string
  error?: string
}

export interface PlanRequest {
  mode: string
  prompt: string
}

export interface ExecuteRequest {
  mode: string
  prompt: string
  debug?: boolean
  force_dummy?: boolean
}

export interface PlanResponse {
  allowed_tools: ToolInfo[]
  planned_calls: PlannedToolCall[]
  summary: string
}

export interface ExecuteResponse {
  success: boolean
  result?: OrchestratorResult
  error?: string
}

export interface ModeInfo {
  name: string
  description: string
  allowed_tools: string[]
}

// API 方法
export const aiOrchestratorApi = {
  /**
   * 获取 Orchestrator 状态
   */
  async getStatus(): Promise<OrchestratorStatus> {
    const response = await axios.get<OrchestratorStatus>(`${API_BASE}/status`)
    return response.data
  },

  /**
   * 生成执行计划（不执行）
   */
  async plan(request: PlanRequest): Promise<PlanResponse> {
    const response = await axios.post<PlanResponse>(`${API_BASE}/plan`, request)
    return response.data
  },

  /**
   * 执行 Orchestrator 流程
   */
  async execute(request: ExecuteRequest): Promise<ExecuteResponse> {
    const response = await axios.post<ExecuteResponse>(`${API_BASE}/execute`, request)
    return response.data
  },

  /**
   * 获取所有可用工具
   */
  async getTools(): Promise<{ tools: Array<{ name: string; description: string; parameters: any }> }> {
    const response = await axios.get(`${API_BASE}/tools`)
    return response.data
  },

  /**
   * 获取所有运行模式
   */
  async getModes(): Promise<{ modes: ModeInfo[] }> {
    const response = await axios.get(`${API_BASE}/modes`)
    return response.data
  },
}

export default aiOrchestratorApi
