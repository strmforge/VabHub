/**
 * 音乐库类型定义
 */

export interface MusicArtist {
  id: number
  name: string
  alt_names?: string[] | null
  country?: string | null
  album_count: number
  track_count: number
}

export interface MusicAlbum {
  id: number
  title: string
  artist_id?: number | null
  artist_name?: string | null
  year?: number | null
  cover_url?: string | null
  track_count: number
  total_duration_seconds?: number | null
  genre?: string | null
}

export interface MusicTrack {
  id: number
  title: string
  artist_id?: number | null
  artist_name?: string | null
  album_id?: number | null
  album_title?: string | null
  track_number?: number | null
  disc_number?: number | null
  duration_seconds?: number | null
  bitrate_kbps?: number | null
  format?: string | null
  file_id?: number | null
}

export interface MusicFile {
  id: number
  music_id: number
  file_path: string
  file_size_bytes?: number | null
  file_size_mb?: number | null
  format: string
  duration_seconds?: number | null
  bitrate_kbps?: number | null
  sample_rate_hz?: number | null
  channels?: number | null
  track_number?: number | null
  disc_number?: number | null
  created_at: string
}

export interface MusicAlbumDetail {
  id: number
  title: string
  artist_id?: number | null
  artist_name?: string | null
  album_artist?: string | null
  year?: number | null
  cover_url?: string | null
  genre?: string | null
  track_count: number
  total_duration_seconds?: number | null
  tracks: MusicTrack[]
}

export interface MusicListResponse {
  items: MusicAlbum[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicArtistListResponse {
  items: MusicArtist[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicTrackListResponse {
  items: MusicTrack[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicStats {
  total_artists: number
  total_albums: number
  total_tracks: number
  total_files: number
  total_size_mb: number
  total_duration_seconds?: number | null
}

// ========== MC2: 榜单相关类型 ==========

export interface MusicChartSource {
  id: number
  platform: string
  display_name: string
  description?: string | null
  config?: Record<string, unknown> | null
  is_enabled: boolean
  icon_url?: string | null
  created_at: string
  updated_at: string
}

export interface MusicChartSourceListResponse {
  items: MusicChartSource[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicChart {
  id: number
  source_id: number
  chart_key: string
  display_name: string
  description?: string | null
  region?: string | null
  chart_type?: string | null
  is_enabled: boolean
  last_fetched_at?: string | null
  fetch_interval_minutes: number
  max_items: number
  created_at: string
  updated_at: string
  source_platform?: string | null
  source_display_name?: string | null
}

export interface MusicChartListResponse {
  items: MusicChart[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicChartItem {
  id: number
  chart_id: number
  rank?: number | null
  title: string
  artist_name: string
  album_name?: string | null
  external_ids?: Record<string, unknown> | null
  duration_seconds?: number | null
  cover_url?: string | null
  external_url?: string | null
  first_seen_at: string
  last_seen_at: string
}

export interface MusicChartItemListResponse {
  items: MusicChartItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MusicChartDetail extends MusicChart {
  items: MusicChartItem[]
}

// ========== MC2: 用户订阅相关类型 ==========

export interface UserMusicSubscription {
  id: number
  user_id: number
  chart_id: number
  status: string
  auto_search: boolean
  auto_download: boolean
  max_new_tracks_per_run: number
  quality_preference?: string | null
  preferred_sites?: string | null
  last_run_at?: string | null
  last_run_new_count?: number | null
  last_run_search_count?: number | null
  last_run_download_count?: number | null
  created_at: string
  updated_at: string
  chart_display_name?: string | null
  source_platform?: string | null
}

export interface UserMusicSubscriptionListResponse {
  items: UserMusicSubscription[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface UserMusicSubscriptionCreate {
  chart_id: number
  auto_search?: boolean
  auto_download?: boolean
  max_new_tracks_per_run?: number
  quality_preference?: string
  preferred_sites?: string
}

export interface UserMusicSubscriptionUpdate {
  status?: string
  auto_search?: boolean
  auto_download?: boolean
  max_new_tracks_per_run?: number
  quality_preference?: string
  preferred_sites?: string
}

export interface SubscriptionRunResult {
  subscription_id: number
  new_items_count: number
  search_count: number
  download_count: number
  failed_count: number
  errors: string[]
}

// ========== MC2: 下载任务相关类型 ==========

export interface MusicDownloadJob {
  id: number
  subscription_id?: number | null
  chart_item_id?: number | null
  user_id: number
  search_query: string
  status: string
  
  // PT 搜索结果
  matched_site?: string | null
  matched_torrent_id?: string | null
  matched_torrent_name?: string | null
  matched_torrent_size_bytes?: number | null
  matched_seeders?: number | null
  matched_leechers?: number | null
  matched_free_percent?: number | null
  quality_score?: number | null
  search_candidates_count?: number | null
  
  // 下载相关
  download_client?: string | null
  download_task_id?: number | null
  downloader_hash?: string | null
  downloaded_path?: string | null
  
  // 导入结果
  music_file_id?: number | null
  music_id?: number | null
  is_duplicate: boolean
  
  // 错误和重试
  last_error?: string | null
  retry_count: number
  max_retries: number
  
  // 时间戳
  created_at: string
  updated_at: string
  started_at?: string | null
  completed_at?: string | null
  
  // 关联信息
  chart_item_title?: string | null
  chart_item_artist?: string | null
  subscription_name?: string | null
}

export interface MusicDownloadJobListResponse {
  items: MusicDownloadJob[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Phase 3: 订阅覆盖统计
export interface SubscriptionCoverageStats {
  subscription_id: number
  chart_id: number
  total_items: number
  ready_count: number
  downloading_count: number
  queued_count: number
  not_queued_count: number
  failed_count: number
}

// Phase 3: 任务状态枚举
export type MusicJobStatus = 
  | 'pending'
  | 'searching'
  | 'found'
  | 'not_found'
  | 'submitted'
  | 'downloading'
  | 'importing'
  | 'completed'
  | 'failed'
  | 'skipped_duplicate'
