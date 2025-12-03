/**
 * 用户通知渠道类型定义
 * NOTIFY-CORE 实现
 */

export type UserNotifyChannelType = 'telegram_bot' | 'webhook' | 'bark'

export interface UserNotifyChannel {
  id: number
  channel_type: UserNotifyChannelType
  display_name?: string | null
  config: Record<string, any>
  is_enabled: boolean
  is_verified: boolean
  last_test_at?: string | null
  last_test_ok?: boolean | null
  last_error?: string | null
  created_at: string
  updated_at: string
}

export interface UserNotifyChannelCreate {
  channel_type: UserNotifyChannelType
  display_name?: string | null
  config?: Record<string, any>
  is_enabled?: boolean
}

export interface UserNotifyChannelUpdate {
  display_name?: string | null
  config?: Record<string, any>
  is_enabled?: boolean
}

export interface UserNotifyChannelTestResponse {
  success: boolean
  message: string
}

// 渠道类型选项
export const channelTypeOptions = [
  { value: 'telegram_bot', title: 'Telegram 机器人', icon: 'mdi-telegram', description: '通过 Telegram Bot 接收通知' },
  { value: 'webhook', title: 'Webhook', icon: 'mdi-webhook', description: '发送 HTTP 请求到自定义 URL' },
  { value: 'bark', title: 'Bark', icon: 'mdi-bell-ring', description: 'iOS 推送通知' },
] as const

// 渠道配置字段定义
export const channelConfigFields: Record<UserNotifyChannelType, { key: string; label: string; type: string; required?: boolean; placeholder?: string }[]> = {
  telegram_bot: [
    // Telegram 通过绑定流程配置，不需要手动输入
  ],
  webhook: [
    { key: 'url', label: 'Webhook URL', type: 'url', required: true, placeholder: 'https://example.com/notify' },
    { key: 'secret', label: 'Secret（可选）', type: 'password', placeholder: '用于验证请求' },
  ],
  bark: [
    { key: 'server', label: '服务器地址', type: 'url', required: true, placeholder: 'https://api.day.app/your-key' },
    { key: 'sound', label: '提示音', type: 'text', placeholder: 'alarm' },
    { key: 'group', label: '分组', type: 'text', placeholder: 'VabHub' },
  ],
}
