/**
 * 系统健康检查类型定义
 * OPS-1E 实现
 */

export type HealthStatus = 'ok' | 'warning' | 'error' | 'unknown'

export interface SystemHealthCheck {
  key: string
  check_type: string
  status: HealthStatus
  last_checked_at: string | null
  last_duration_ms: number | null
  last_error: string | null
  meta?: Record<string, unknown> | null
}

export interface SystemRunnerStatus {
  name: string
  runner_type: string
  last_started_at: string | null
  last_finished_at: string | null
  last_exit_code: number | null
  last_duration_ms: number | null
  last_error: string | null
  recommended_interval_min: number | null
  success_count: number
  failure_count: number
}

export interface RunnerStats {
  name: string
  runner_type: string
  last_started_at: string | null
  last_finished_at: string | null
  last_exit_code: number | null
  last_duration_ms: number | null
  last_error: string | null
  recommended_interval_min: number | null
  success_count: number
  failure_count: number
  total_runs: number
  success_rate: number
}

export interface SystemHealthSummary {
  overall_status: HealthStatus
  total_checks: number
  ok_count: number
  warning_count: number
  error_count: number
  unknown_count: number
  checks: SystemHealthCheck[]
  runners: SystemRunnerStatus[]
  last_check_time: string | null
}

// 状态颜色映射
export const healthStatusColors: Record<HealthStatus, string> = {
  ok: 'success',
  warning: 'warning',
  error: 'error',
  unknown: 'grey',
}

// 状态图标映射
export const healthStatusIcons: Record<HealthStatus, string> = {
  ok: 'mdi-check-circle',
  warning: 'mdi-alert',
  error: 'mdi-alert-circle',
  unknown: 'mdi-help-circle',
}

// 状态文本映射
export const healthStatusTexts: Record<HealthStatus, string> = {
  ok: '正常',
  warning: '警告',
  error: '错误',
  unknown: '未知',
}
