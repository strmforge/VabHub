/**
 * 通知偏好类型定义
 * NOTIFY-UX-1 实现
 */

// 通知类型枚举
export type NotificationType =
  | 'MANGA_NEW_CHAPTER'
  | 'MANGA_UPDATED'
  | 'MANGA_SYNC_FAILED'
  | 'NOVEL_NEW_CHAPTER'
  | 'AUDIOBOOK_NEW_TRACK'
  | 'TTS_JOB_COMPLETED'
  | 'TTS_JOB_FAILED'
  | 'AUDIOBOOK_READY'
  | 'MUSIC_CHART_UPDATED'
  | 'MUSIC_NEW_TRACKS_QUEUED'
  | 'MUSIC_NEW_TRACKS_DOWNLOADING'
  | 'MUSIC_NEW_TRACKS_READY'
  | 'SYSTEM_MESSAGE'

// 媒体类型
export type ReadingMediaType = 'NOVEL' | 'AUDIOBOOK' | 'MANGA'

// 通知类型信息
export interface NotificationTypeInfo {
  type: NotificationType
  name: string
  description: string
  group: string // manga / novel / music / system / task
  is_critical: boolean
}

// 用户通知偏好
export interface UserNotifyPreference {
  id: number
  user_id: number
  notification_type: NotificationType
  media_type?: ReadingMediaType | null
  target_id?: number | null
  enable_web: boolean
  enable_telegram: boolean
  enable_webhook: boolean
  enable_bark: boolean
  muted: boolean
  digest_only: boolean
  created_at: string
  updated_at: string
}

// 用户静音状态
export interface UserNotifySnooze {
  id: number
  user_id: number
  muted: boolean
  snooze_until?: string | null
  allow_critical_only: boolean
  created_at: string
  updated_at: string
}

// 偏好矩阵（聚合）
export interface UserNotifyPreferenceMatrix {
  preferences: UserNotifyPreference[]
  snooze?: UserNotifySnooze | null
  available_notification_types: NotificationTypeInfo[]
}

// 创建/更新偏好请求
export interface UserNotifyPreferenceUpsert {
  notification_type: NotificationType
  media_type?: ReadingMediaType | null
  target_id?: number | null
  enable_web?: boolean
  enable_telegram?: boolean
  enable_webhook?: boolean
  enable_bark?: boolean
  muted?: boolean
  digest_only?: boolean
}

// 更新静音请求
export interface UserNotifySnoozeUpdate {
  muted?: boolean
  snooze_until?: string | null
  allow_critical_only?: boolean
}

// 快速 Snooze 请求
export interface SnoozeRequest {
  duration_minutes?: number // 5-1440
  until?: string
  allow_critical_only?: boolean
}

// 静音某类通知请求
export interface MuteNotificationTypeRequest {
  notification_type: NotificationType
  media_type?: ReadingMediaType | null
  target_id?: number | null
}

// 通知类型分组配置（前端展示用）
export const NOTIFICATION_TYPE_GROUPS: Record<string, {
  label: string
  icon: string
  color: string
}> = {
  manga: {
    label: '漫画',
    icon: 'mdi-book-open-page-variant',
    color: 'orange',
  },
  novel: {
    label: '小说/有声书',
    icon: 'mdi-book',
    color: 'blue',
  },
  music: {
    label: '音乐',
    icon: 'mdi-music',
    color: 'purple',
  },
  system: {
    label: '系统',
    icon: 'mdi-cog',
    color: 'grey',
  },
}
