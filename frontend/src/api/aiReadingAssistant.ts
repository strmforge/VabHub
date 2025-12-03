/**
 * AI 阅读助手 API
 *
 * FUTURE-AI-READING-ASSISTANT-1 P4 实现
 */

import axios from 'axios'

const API_BASE = '/api/ai/reading-assistant'

// ==================== 类型定义 ====================

export type ReadingGoalType = 'daily' | 'weekly' | 'monthly' | 'yearly'
export type SuggestionType = 'continue' | 'start' | 'finish' | 'pause'
export type SuggestionPriority = 'high' | 'medium' | 'low'

export interface ReadingGoal {
  goal_type: ReadingGoalType
  target_count: number
  current_count: number
  media_types: string[]
  deadline?: string
  description: string
}

export interface ReadingSuggestion {
  suggestion_type: SuggestionType
  media_type: string
  item_id?: number
  title: string
  author?: string
  reason: string
  priority: SuggestionPriority
  estimated_time?: string
  current_progress?: string
}

export interface ReadingPlanDraft {
  summary: string
  goals: ReadingGoal[]
  suggestions: ReadingSuggestion[]
  stats_context: Record<string, any>
  insights: string[]
  generated_at?: string
}

export interface ReadingPlanRequest {
  prompt?: string
  focus?: string // 'all' | 'novel' | 'manga' | 'audiobook'
  goal_type?: string // 'daily' | 'weekly' | 'monthly'
}

export interface ReadingPlanResponse {
  success: boolean
  plan?: ReadingPlanDraft
  error?: string
}

export interface PresetReadingPrompt {
  id: string
  title: string
  prompt: string
  description: string
  focus?: string
}

export interface PresetReadingPromptsResponse {
  prompts: PresetReadingPrompt[]
}

export interface ServiceStatus {
  enabled: boolean
  service: string
  version: string
  features: string[]
  supported_media_types: string[]
}

// ==================== API 方法 ====================

export const aiReadingAssistantApi = {
  /**
   * 生成阅读计划草案
   */
  async generate(request: ReadingPlanRequest): Promise<ReadingPlanResponse> {
    const response = await axios.post<ReadingPlanResponse>(`${API_BASE}/generate`, request)
    return response.data
  },

  /**
   * 获取预设提示词
   */
  async getPresetPrompts(): Promise<PresetReadingPromptsResponse> {
    const response = await axios.get<PresetReadingPromptsResponse>(`${API_BASE}/preset-prompts`)
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

export default aiReadingAssistantApi
