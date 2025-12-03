/**
 * 阅读中心类型定义
 */

export type ReadingMediaType = 'NOVEL' | 'AUDIOBOOK' | 'MANGA'

// 阅读状态
export type ReadingStatus = 'not_started' | 'in_progress' | 'finished'

// 活动类型
export type ActivityType = 'read' | 'listen' | 'update'

export interface ReadingOngoingItem {
  media_type: ReadingMediaType
  item_id: number
  title: string
  sub_title?: string | null
  cover_url?: string | null
  source_label?: string | null
  progress_label: string
  progress_percent?: number | null
  status: ReadingStatus
  is_finished: boolean
  last_read_at: string
  last_activity_at?: string | null
  update_reason?: string | null
  route_name: string
  route_params: Record<string, any>
}

export interface ReadingHistoryItem {
  media_type: ReadingMediaType
  item_id: number
  title: string
  sub_title?: string | null
  cover_url?: string | null
  source_label?: string | null
  last_position_label: string
  progress_percent?: number | null
  status: ReadingStatus
  is_finished: boolean
  last_read_at: string
  last_activity_at?: string | null
  route_name: string
  route_params: Record<string, any>
}

export interface ReadingActivityItem {
  media_type: ReadingMediaType
  item_id: number
  title: string
  sub_title?: string | null
  cover_url?: string | null
  status: ReadingStatus
  activity_type: ActivityType
  activity_label: string
  occurred_at: string
  route_name: string
  route_params: Record<string, any>
}

export interface ReadingStats {
  ongoing_count: number
  finished_count: number
  finished_count_recent_30d: number
  favorites_count: number
  recent_activity_count: number
  by_type: {
    NOVEL?: { ongoing: number; finished: number; recent_finished: number; recent_activity: number }
    AUDIOBOOK?: { ongoing: number; finished: number; recent_finished: number; recent_activity: number }
    MANGA?: { ongoing: number; finished: number; recent_finished: number; recent_activity: number }
  }
}

