/**
 * 设置相关类型定义
 */

export interface InboxSettings {
  inbox_root: string
  enabled: boolean
  enabled_media_types: string[]
  detection_min_score: number
  scan_max_items: number
  last_run_at: string | null
  last_run_status: 'never' | 'success' | 'partial' | 'failed' | 'empty'
  last_run_summary: string | null
  pending_warning: string | null
}

export interface LibraryRootsSettings {
  movie: string
  tv: string
  anime: string
  short_drama?: string | null
  ebook: string
  comic?: string | null
  music?: string | null
}

export interface LibrarySettingsResponse {
  inbox: InboxSettings
  library_roots: LibraryRootsSettings
}

// ========== TTS Settings ==========

export interface TTSRateLimitInfo {
  max_daily_requests: number
  max_daily_characters: number
  max_requests_per_run: number
  last_limited_at: string | null
  last_limited_reason: string | null
}

export interface TTSUsageStats {
  total_tts_audiobooks: number
  by_provider: Record<string, number>
}

export interface TTSVoicePresetUsage {
  id: number
  name: string
  provider?: string | null
  language?: string | null
  voice?: string | null
  is_default: boolean
  bound_works_count: number
  tts_generated_works_count: number
  last_used_at?: string | null
  // 热度指标
  usage_ratio?: number
  heat_level?: 'hot' | 'sleeping' | 'cold' | 'normal'
  is_hot?: boolean
  is_sleeping?: boolean
  is_cold?: boolean
}

export interface TTSWorkProfileSummary {
  works_total: number
  works_with_profile: number
  works_without_profile: number
  works_with_preset: number
  works_without_preset: number
}

export interface TTSStorageAutoCleanupInfo {
  enabled: boolean
  last_run_at: string | null
  last_run_status: 'success' | 'skipped' | 'failed' | null
  last_run_freed_bytes: number
  last_run_reason: string | null
}

export interface TTSStorageOverviewSummary {
  root: string
  total_files: number
  total_size_bytes: number
  warning: 'ok' | 'high_usage' | 'critical' | 'no_root' | 'scan_error'
  auto_cleanup?: TTSStorageAutoCleanupInfo
}

export interface TTSSettings {
  enabled: boolean
  provider: string
  status: 'disabled' | 'ok' | 'degraded'
  output_root?: string | null
  max_chapters?: number | null
  strategy?: string | null
  last_used_at?: string | null
  last_error?: string | null
  rate_limit_enabled: boolean
  rate_limit_info?: TTSRateLimitInfo | null
  usage_stats: TTSUsageStats
  preset_usage: TTSVoicePresetUsage[]
  work_profile_summary?: TTSWorkProfileSummary | null
  storage_overview?: TTSStorageOverviewSummary | null
}

