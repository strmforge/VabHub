// 通知相关类型定义
// BOT-EXT-2 增强：支持 NotificationAction
// NOTIFY-CENTER-2 增强：支持通知分类

// 通知分类枚举
export type NotificationCategory = 
  | 'reading'      // 阅读相关：漫画、小说、有声书
  | 'download'     // 下载相关：音乐下载、文件下载
  | 'music'        // 音乐相关：榜单更新、新音乐
  | 'plugin'       // 插件相关：插件安装、更新、错误
  | 'system'       // 系统相关：系统消息、版本更新、错误
  | 'other'        // 其他未分类通知

// 通知类型枚举
export type NotificationType = 
  | 'info' | 'success' | 'warning' | 'error' 
  | 'MANGA_NEW_CHAPTER' | 'MANGA_UPDATED' | 'MANGA_SYNC_FAILED'
  | 'NOVEL_NEW_CHAPTER' | 'AUDIOBOOK_NEW_TRACK' 
  | 'SYSTEM_MESSAGE' | 'TTS_JOB_COMPLETED' | 'TTS_JOB_FAILED' | 'AUDIOBOOK_READY'
  | 'READING_EBOOK_IMPORTED'
  | 'DOWNLOAD_SUBSCRIPTION_MATCHED' | 'DOWNLOAD_TASK_COMPLETED' | 'DOWNLOAD_HR_RISK'

// 媒体类型枚举
export type MediaType = 'manga' | 'novel' | 'audiobook' | 'ebook'

// 通知来源分类
export type NotificationSource = 
  | 'SYSTEM' 
  | 'TTS' 
  | 'AUDIOBOOK' 
  | 'MANGA' 
  | 'NOVEL' 
  | 'OTHER'

// 通知严重程度
export type NotificationLevel = 'info' | 'success' | 'warning' | 'error'

// 通知动作类型枚举
export type NotificationActionType =
  | 'open_web_url'
  | 'open_web_route'
  | 'api_call'
  | 'mark_as_read'
  | 'open_reading_center'
  | 'open_manga'
  | 'open_novel'
  | 'open_audiobook'
  | 'open_music_center'
  | 'download'
  | 'subscribe'
  | 'retry'

// 通知动作结构
export interface NotificationAction {
  id: string
  label: string
  type: NotificationActionType
  icon?: string
  primary?: boolean
  url?: string
  route_name?: string
  route_params?: Record<string, any>
  route_query?: Record<string, any>
  api_path?: string
  api_method?: string
  api_body?: Record<string, any>
  media_type?: string
  target_id?: number
  extra?: Record<string, any>
}

// 通知列表查询参数
export interface NotificationListQuery {
  limit?: number
  offset?: number
  type?: string
  media_type?: string
  is_read?: boolean
  level?: NotificationLevel
}

// 通知 payload 结构
export interface NotificationPayload {
  route_name?: string
  route_params?: Record<string, any>
  job_id?: number
  ebook_id?: number
  extra?: Record<string, any>
  cover_url?: string
  source_label?: string
  total_new_count?: number
  total_chapters?: number
  // 下载通知相关字段
  notification_type?: string
  subscription_name?: string
  file_size_gb?: number
  download_duration_minutes?: number
  category_label?: string
  risk_level?: string
  reason?: string
  min_seed_time_hours?: number
  task_id?: number
  success?: boolean
  media_type?: string
  season_number?: number
  episode_number?: number
  library_path?: string
  subscription_id?: number
  torrent_id?: number
  rule_labels?: string[]
}

export interface UserNotification {
  id: number
  user_id: number
  title: string
  message?: string
  type: NotificationType
  media_type?: MediaType
  target_id?: number
  sub_target_id?: number
  payload?: NotificationPayload
  is_read: boolean
  created_at: string
  updated_at: string
  read_at?: string
}

export interface UserNotificationItem {
  id: number
  title: string
  message?: string
  type: NotificationType
  category: NotificationCategory
  media_type?: MediaType
  target_id?: number
  sub_target_id?: number
  payload?: NotificationPayload
  is_read: boolean
  created_at: string
  updated_at: string
  read_at?: string
  severity?: string
  ebook_id?: number
  tts_job_id?: number
  // BOT-EXT-2: 动作列表
  actions?: NotificationAction[]
}

export interface UserNotificationListResponse {
  items: UserNotificationItem[]  // 修复：应该是 UserNotificationItem[] 而不是 UserNotification[]
  total: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface MarkReadResponse {
  success: boolean
  updated: number
}

export interface MarkAllReadResponse {
  updated: number
}

// 通知统计摘要
export interface NotificationSummary {
  total_unread: number
  unread_by_level: {
    error: number
    warning: number
    success: number
    info: number
  }
}

/**
 * 根据通知内容推断来源
 */
export function inferNotificationSource(n: UserNotificationItem): NotificationSource {
  // 根据事件类型推断
  if (n.type === 'TTS_JOB_COMPLETED' || n.type === 'TTS_JOB_FAILED') {
    return 'TTS'
  }
  if (n.type === 'AUDIOBOOK_READY' || n.type === 'AUDIOBOOK_NEW_TRACK') {
    return 'AUDIOBOOK'
  }
  if (n.type === 'MANGA_NEW_CHAPTER' || n.type === 'MANGA_UPDATED' || n.type === 'MANGA_SYNC_FAILED') {
    return 'MANGA'
  }
  if (n.type === 'NOVEL_NEW_CHAPTER') {
    return 'NOVEL'
  }
  if (n.type === 'SYSTEM_MESSAGE') {
    return 'SYSTEM'
  }
  
  // 根据媒体类型推断
  if (n.media_type === 'manga') {
    return 'MANGA'
  }
  if (n.media_type === 'novel') {
    return 'NOVEL'
  }
  if (n.media_type === 'audiobook') {
    return 'AUDIOBOOK'
  }
  
  // 根据标题和消息关键词推断
  const title = n.title?.toLowerCase() || ''
  const message = n.message?.toLowerCase() || ''
  
  if (title.includes('tts') || message.includes('tts')) {
    return 'TTS'
  }
  if (title.includes('有声书') || message.includes('有声书')) {
    return 'AUDIOBOOK'
  }
  if (title.includes('漫画') || message.includes('漫画')) {
    return 'MANGA'
  }
  if (title.includes('小说') || message.includes('小说')) {
    return 'NOVEL'
  }
  if (title.includes('系统') || message.includes('系统')) {
    return 'SYSTEM'
  }
  
  return 'OTHER'
}