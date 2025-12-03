/**
 * AI 整理顾问 API
 *
 * FUTURE-AI-CLEANUP-ADVISOR-1 P4 实现
 */

import axios from 'axios'

const API_BASE = '/api/ai/cleanup-advisor'

// ==================== 类型定义 ====================

export type RiskLevel = 'safe' | 'caution' | 'risky'
export type CleanupActionType = 'delete' | 'archive' | 'transcode' | 'replace'

export interface CleanupAction {
  id: string
  action_type: CleanupActionType
  target_type: string
  target_id: string
  target_title: string
  target_path?: string
  size_gb: number
  reason: string
  risk_level: RiskLevel
  risk_notes: string[]
  hr_status?: string
}

export interface CleanupPlanDraft {
  summary: string
  total_savable_gb: number
  actions: CleanupAction[]
  storage_context: Record<string, any>
  warnings: string[]
  generated_at?: string
}

export interface CleanupRequest {
  prompt?: string
  focus?: string // 'all' | 'downloads' | 'duplicates' | 'low_quality' | 'seeding'
  min_size_gb?: number
  include_risky?: boolean
}

export interface CleanupResponse {
  success: boolean
  draft?: CleanupPlanDraft
  error?: string
}

export interface PresetCleanupPrompt {
  id: string
  title: string
  prompt: string
  description: string
  focus?: string
}

export interface PresetCleanupPromptsResponse {
  prompts: PresetCleanupPrompt[]
}

export interface ServiceStatus {
  enabled: boolean
  service: string
  version: string
  features: string[]
  constraints: string[]
}

// ==================== API 方法 ====================

export const aiCleanupAdvisorApi = {
  /**
   * 生成清理计划草案
   */
  async generate(request: CleanupRequest): Promise<CleanupResponse> {
    const response = await axios.post<CleanupResponse>(`${API_BASE}/generate`, request)
    return response.data
  },

  /**
   * 获取预设提示词
   */
  async getPresetPrompts(): Promise<PresetCleanupPromptsResponse> {
    const response = await axios.get<PresetCleanupPromptsResponse>(`${API_BASE}/preset-prompts`)
    return response.data
  },

  /**
   * 检查服务状态
   */
  async getServiceStatus(): Promise<ServiceStatus> {
    const response = await axios.get<ServiceStatus>(`${API_BASE}/status`)
    return response.data
  },
}

export default aiCleanupAdvisorApi
