/**
 * 电视墙类型定义
 */

export interface PlayerWallWorkSummary {
  id: number
  title: string
  year?: number
  media_type: string
  poster_url?: string
  overview?: string
  tmdb_id?: number | null
}

export interface PlayerWallSourceInfo {
  has_local: boolean
  has_115: boolean
}

export interface PlayerWallStatusInfo {
  // 订阅状态
  has_subscription: boolean
  subscription_status?: 'active' | 'completed' | 'paused'
  
  // 下载状态
  has_active_downloads: boolean
  download_count?: number
  
  // 入库状态
  library_status: 'in_library' | 'partial' | 'not_in_library'
  
  // HR风险状态
  hr_risk: boolean
  hr_level?: 'low' | 'medium' | 'high'
  
  // 播放进度
  has_progress: boolean
  progress_percent?: number
  is_finished: boolean
}

export interface PlayerWallItem {
  work: PlayerWallWorkSummary
  source: PlayerWallSourceInfo
  status: PlayerWallStatusInfo
}

export interface TvWallSmartOpenDecision {
  kind: 'media_library' | 'vabhub_detail'
  url?: string | null
  route_name?: string | null
  route_params?: Record<string, any> | null
  reason?: string | null
  fallback_available: boolean
}

export interface TvWallSmartOpenResponse {
  network_context: 'lan' | 'wan' | 'unknown'
  decision: TvWallSmartOpenDecision
}

export interface TvWallSmartOpenRequest {
  media_id: number | string
  media_type: string
}

