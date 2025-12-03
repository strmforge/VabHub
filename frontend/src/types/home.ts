/**
 * 首页仪表盘类型定义
 * HOME-1 实现
 */

export interface HomeQuickStat {
  label: string
  value: number
  icon?: string | null  // mdi- 开头
  color?: string | null  // primary / secondary / success / error / info / warning
}

export interface HomeUpNextItem {
  media_type: string  // "movie" | "series" | "novel" | "audiobook" | "manga" | "music"
  title: string
  sub_title?: string | null
  cover_url?: string | null
  progress_percent?: number | null
  last_activity_at?: string | null
  route_name?: string | null
  route_params?: Record<string, any> | null
}

export interface HomeRecentItem {
  media_type: string
  title: string
  sub_title?: string | null
  cover_url?: string | null
  created_at?: string | null
  route_name?: string | null
  route_params?: Record<string, any> | null
}

export interface HomeRunnerStatus {
  name: string
  key: string
  last_run_at?: string | null
  last_status?: string | null  // "success" | "failed" | "unknown"
  last_message?: string | null
}

export interface HomeTaskSummary {
  total_running: number
  total_failed_recent: number
  total_waiting: number
}

export interface HomeDashboardResponse {
  stats: HomeQuickStat[]
  up_next: HomeUpNextItem[]
  recent_items: HomeRecentItem[]
  runners: HomeRunnerStatus[]
  tasks: HomeTaskSummary
}
