/**
 * 任务中心类型定义
 * TASK-1 实现
 */

export type TaskMediaType = 'movie' | 'series' | 'novel' | 'audiobook' | 'manga' | 'music' | 'other'
export type TaskKind = 'download' | 'tts' | 'import' | 'subscription' | 'other'
export type TaskStatus = 'pending' | 'running' | 'success' | 'failed' | 'skipped'

export interface TaskCenterItem {
  id: string
  kind: TaskKind
  media_type: TaskMediaType
  title: string
  sub_title?: string | null
  status: TaskStatus
  progress?: number | null  // 0-100
  created_at?: string | null
  updated_at?: string | null
  last_error?: string | null
  source?: string | null
  route_name?: string | null
  route_params?: Record<string, any> | null
}

export interface TaskCenterListResponse {
  items: TaskCenterItem[]
  total: number
}
