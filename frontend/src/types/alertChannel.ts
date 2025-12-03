/**
 * 告警渠道类型定义
 * OPS-2A 实现
 */

export type AlertChannelType = 'telegram' | 'webhook' | 'bark'

export type AlertSeverity = 'info' | 'warning' | 'error'

export interface AlertChannel {
  id: number
  name: string
  channel_type: AlertChannelType
  is_enabled: boolean
  min_severity: AlertSeverity
  config: Record<string, any>
  include_checks?: string[] | null
  exclude_checks?: string[] | null
  created_at: string
  updated_at: string
}

export interface AlertChannelCreate {
  name: string
  channel_type: AlertChannelType
  is_enabled?: boolean
  min_severity?: AlertSeverity
  config?: Record<string, any>
  include_checks?: string[] | null
  exclude_checks?: string[] | null
}

export interface AlertChannelUpdate {
  name?: string
  is_enabled?: boolean
  min_severity?: AlertSeverity
  config?: Record<string, any>
  include_checks?: string[] | null
  exclude_checks?: string[] | null
}

// 渠道类型选项
export const channelTypeOptions = [
  { value: 'telegram', title: 'Telegram', icon: 'mdi-telegram' },
  { value: 'webhook', title: 'Webhook', icon: 'mdi-webhook' },
  { value: 'bark', title: 'Bark', icon: 'mdi-bell-ring' },
] as const

// 严重级别选项
export const severityOptions = [
  { value: 'info', title: '信息', color: 'info' },
  { value: 'warning', title: '警告', color: 'warning' },
  { value: 'error', title: '错误', color: 'error' },
] as const

// 渠道配置字段定义
export const channelConfigFields: Record<AlertChannelType, { key: string; label: string; type: string; required?: boolean }[]> = {
  telegram: [
    { key: 'bot_token', label: 'Bot Token', type: 'password', required: true },
    { key: 'chat_id', label: 'Chat ID', type: 'text', required: true },
  ],
  webhook: [
    { key: 'url', label: 'Webhook URL', type: 'url', required: true },
    { key: 'method', label: 'HTTP 方法', type: 'select' },
  ],
  bark: [
    { key: 'server', label: '服务器地址', type: 'url', required: true },
    { key: 'sound', label: '提示音', type: 'text' },
    { key: 'group', label: '分组', type: 'text' },
  ],
}
