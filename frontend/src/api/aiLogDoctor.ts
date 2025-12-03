/**
 * AI 故障医生 API
 *
 * FUTURE-AI-LOG-DOCTOR-1 P4 实现
 */

import axios from 'axios'

const API_BASE = '/api/ai/log-doctor'

// ==================== 类型定义 ====================

export type DiagnosisSeverity = 'info' | 'warning' | 'error' | 'critical'

export interface DiagnosisItem {
  id: string
  severity: DiagnosisSeverity
  title: string
  description: string
  evidence: string[]
  related_components: string[]
}

export interface DiagnosisPlanStep {
  step: number
  title: string
  detail: string
  is_safe: boolean
}

export interface SystemDiagnosisReport {
  overall_status: DiagnosisSeverity
  summary: string
  items: DiagnosisItem[]
  suggested_steps: DiagnosisPlanStep[]
  raw_refs?: Record<string, any>
  generated_at?: string
}

export interface DiagnoseRequest {
  prompt?: string
  time_window?: string // '1h' | '24h' | '7d'
  focus?: string // 'all' | 'download' | 'rsshub' | 'site' | 'runner' | 'telegram' | 'storage'
}

export interface DiagnoseResponse {
  success: boolean
  report?: SystemDiagnosisReport
  error?: string
}

export interface PresetPrompt {
  id: string
  title: string
  prompt: string
  description: string
  focus?: string
}

export interface PresetPromptsResponse {
  prompts: PresetPrompt[]
}

export interface ServiceStatus {
  enabled: boolean
  service: string
  version: string
  features: string[]
}

// ==================== API 方法 ====================

export const aiLogDoctorApi = {
  /**
   * 执行系统诊断
   */
  async diagnose(request: DiagnoseRequest): Promise<DiagnoseResponse> {
    const response = await axios.post<DiagnoseResponse>(`${API_BASE}/diagnose`, request)
    return response.data
  },

  /**
   * 获取预设提示词
   */
  async getPresetPrompts(): Promise<PresetPromptsResponse> {
    const response = await axios.get<PresetPromptsResponse>(`${API_BASE}/preset-prompts`)
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

export default aiLogDoctorApi
