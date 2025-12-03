/**
 * Dashboard相关类型定义
 */

export interface SystemStats {
  cpu_usage: number
  memory_usage: number
  memory_total_gb: number
  memory_used_gb: number
  disk_usage: number
  disk_total_gb: number
  disk_used_gb: number
  disk_free_gb: number
  network_sent: number
  network_recv: number
}

export interface MediaStats {
  total_movies: number
  total_tv_shows: number
  total_anime: number
  total_episodes: number
  total_size_gb: number
  by_quality: Record<string, number>
}

export interface DownloadStats {
  active: number
  paused: number
  completed: number
  failed: number
  total_speed_mbps: number
  total_size_gb: number
  downloaded_gb: number
}

export interface TTSStats {
  pending_jobs: number
  running_jobs: number
  completed_last_24h: number
}

export interface PluginStats {
  total_plugins: number
  active_plugins: number
  quarantined_plugins: number
}

export interface ReadingStats {
  active_novels: number
  active_audiobooks: number
  active_manga: number
}

export interface RecentEvent {
  type: string
  title: string
  time: string | null
  message: string
  media_type?: string
  ebook_id?: number
  plugin_name?: string
}

export interface DashboardData {
  system_stats: SystemStats
  media_stats: MediaStats
  download_stats: DownloadStats
  active_downloads: number
  active_subscriptions: number
  tts_stats: TTSStats
  plugin_stats: PluginStats
  reading_stats: ReadingStats
  recent_events: RecentEvent[]
}
