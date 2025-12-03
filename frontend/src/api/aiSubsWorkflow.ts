/**
 * AI 订阅工作流 API
 *
 * FUTURE-AI-SUBS-WORKFLOW-1 P4 实现
 * 提供 AI 订阅助手的前端 API 调用
 */

import axios from 'axios'

const API_BASE = '/api/ai/subs-workflow'

// ==================== 类型定义 ====================

export type SubsTargetMediaType = 'movie' | 'tv' | 'anime' | 'short_drama' | 'music' | 'book' | 'comic'
export type SubsSourceType = 'rsshub' | 'pt_search' | 'rss_url'

export interface SubsWorkflowSource {
  type: SubsSourceType
  id?: string
  name?: string
  extra_params?: Record<string, any>
  valid?: boolean
  validation_message?: string
}

export interface SubsFilterRule {
  include_keywords?: string[]
  exclude_keywords?: string[]
  min_resolution?: string
  preferred_resolution?: string
  effect?: string
  hr_safe?: boolean
  free_only?: boolean
  languages?: string[]
  min_seeders?: number
  other_constraints?: Record<string, any>
}

export interface SubsActionConfig {
  download_enabled?: boolean
  dry_run?: boolean
  target_library?: string
  notify_on_match?: boolean
  downloader?: string
  best_version?: boolean
}

export interface SubsWorkflowDraft {
  name: string
  description?: string
  media_type: SubsTargetMediaType
  sources?: SubsWorkflowSource[]
  filter_rule?: SubsFilterRule
  action?: SubsActionConfig
  ai_explanation?: string
  valid?: boolean
  validation_warnings?: string[]
  validation_errors?: string[]
}

export interface PlannedToolCall {
  tool_name: string
  arguments: Record<string, any>
  status: 'pending' | 'success' | 'failed' | 'skipped'
  error?: string
}

// ==================== 请求/响应类型 ====================

export interface PreviewRequest {
  prompt: string
  media_type_hint?: SubsTargetMediaType
  language_hint?: string
  force_dummy?: boolean
}

export interface PreviewResponse {
  success: boolean
  drafts: SubsWorkflowDraft[]
  summary: string
  notes?: string
  orchestrator_plan?: PlannedToolCall[]
  error?: string
}

export interface ApplyRequest {
  draft: SubsWorkflowDraft
  confirm: boolean
}

export interface ApplyResponse {
  success: boolean
  subscription_id?: number
  subscription_name?: string
  rsshub_subscriptions_created: number
  warnings: string[]
  error?: string
}

export interface MediaTypeInfo {
  value: string
  label: string
  supported: boolean
}

export interface PromptExample {
  prompt: string
  description: string
  media_type: string
}

// ==================== API 方法 ====================

export const aiSubsWorkflowApi = {
  /**
   * 预览订阅工作流草案
   */
  async preview(request: PreviewRequest): Promise<PreviewResponse> {
    const response = await axios.post<PreviewResponse>(`${API_BASE}/preview`, request)
    return response.data
  },

  /**
   * 应用订阅工作流草案
   */
  async apply(request: ApplyRequest): Promise<ApplyResponse> {
    const response = await axios.post<ApplyResponse>(`${API_BASE}/apply`, request)
    return response.data
  },

  /**
   * 获取支持的媒体类型
   */
  async getMediaTypes(): Promise<{ media_types: MediaTypeInfo[]; version: string; note: string }> {
    const response = await axios.get(`${API_BASE}/media-types`)
    return response.data
  },

  /**
   * 获取提示词示例
   */
  async getPromptExamples(): Promise<{ examples: PromptExample[]; tips: string[] }> {
    const response = await axios.get(`${API_BASE}/prompt-examples`)
    return response.data
  },
}

export default aiSubsWorkflowApi
