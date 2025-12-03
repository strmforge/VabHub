import api from './api'

// 音乐订阅相关接口定义
export interface UserMusicSubscription {
  id: number
  user_id: number
  subscription_type: 'chart' | 'keyword'
  
  // 榜单订阅字段（仅chart类型使用）
  chart_id?: number | null
  
  // 关键字订阅字段（仅keyword类型使用）
  music_query?: string | null
  music_site?: string | null
  music_quality?: string | null
  
  // 通用字段
  status: 'active' | 'paused'
  auto_search: boolean
  auto_download: boolean
  max_new_tracks_per_run: number
  quality_preference?: string | null
  preferred_sites?: string | null
  
  // 安全策略字段
  allow_hr: boolean
  allow_h3h5: boolean
  strict_free_only: boolean
  
  // 运行统计
  last_run_at?: string | null
  last_run_new_count?: number | null
  last_run_search_count?: number | null
  last_run_download_count?: number | null
  
  // 时间戳
  created_at: string
  updated_at: string
  
  // 关联信息（前端显示用）
  chart_display_name?: string | null
  source_platform?: string | null
}

export interface UserMusicSubscriptionCreate {
  subscription_type?: 'chart' | 'keyword'
  
  // 榜单订阅字段（仅chart类型使用）
  chart_id?: number | null
  
  // 关键字订阅字段（仅keyword类型使用）
  music_query?: string | null
  music_site?: string | null
  music_quality?: string | null
  
  // 通用字段
  auto_search?: boolean
  auto_download?: boolean
  max_new_tracks_per_run?: number
  quality_preference?: string | null
  preferred_sites?: string | null
  
  // 安全策略字段
  allow_hr?: boolean
  allow_h3h5?: boolean
  strict_free_only?: boolean
}

export interface UserMusicSubscriptionUpdate {
  subscription_type?: 'chart' | 'keyword'
  
  // 榜单订阅字段（仅chart类型使用）
  chart_id?: number | null
  
  // 关键字订阅字段（仅keyword类型使用）
  music_query?: string | null
  music_site?: string | null
  music_quality?: string | null
  
  // 通用字段
  status?: 'active' | 'paused'
  auto_search?: boolean
  auto_download?: boolean
  max_new_tracks_per_run?: number
  quality_preference?: string | null
  preferred_sites?: string | null
  
  // 安全策略字段
  allow_hr?: boolean
  allow_h3h5?: boolean
  strict_free_only?: boolean
}

export interface UserMusicSubscriptionListResponse {
  items: UserMusicSubscription[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SubscriptionRunResult {
  subscription_id: number
  new_items_count: number
  search_count: number
  download_count: number
  failed_count: number
  errors: string[]
}

// API调用函数
export async function fetchMusicSubscriptions(params: {
  status?: 'active' | 'paused'
  subscription_type?: 'chart' | 'keyword'
  page?: number
  page_size?: number
} = {}): Promise<UserMusicSubscriptionListResponse> {
  const response = await api.get('/music/subscriptions', { params })
  return response.data
}

export async function createMusicSubscription(data: UserMusicSubscriptionCreate): Promise<UserMusicSubscription> {
  const response = await api.post('/music/subscriptions', data)
  return response.data
}

export async function getMusicSubscription(id: number): Promise<UserMusicSubscription> {
  const response = await api.get(`/music/subscriptions/${id}`)
  return response.data
}

export async function updateMusicSubscription(id: number, data: UserMusicSubscriptionUpdate): Promise<UserMusicSubscription> {
  const response = await api.put(`/music/subscriptions/${id}`, data)
  return response.data
}

export async function deleteMusicSubscription(id: number): Promise<void> {
  await api.delete(`/music/subscriptions/${id}`)
}

export async function runMusicSubscriptionOnce(id: number): Promise<SubscriptionRunResult> {
  const response = await api.post(`/music/subscriptions/${id}/run_once`)
  return response.data
}

export async function pauseMusicSubscription(id: number): Promise<void> {
  await api.post(`/music/subscriptions/${id}/pause`)
}

export async function resumeMusicSubscription(id: number): Promise<void> {
  await api.post(`/music/subscriptions/${id}/resume`)
}

// 音乐榜单相关接口（用于榜单订阅）
export interface MusicChart {
  id: number
  source_id: number
  chart_type: string
  region: string
  display_name: string
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  source?: MusicChartSource | null  // 关联的榜单源信息
}

export interface MusicChartSource {
  id: number
  platform: string
  name: string
  base_url?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export async function fetchMusicCharts(params: {
  platform?: string
  chart_type?: string
  region?: string
  is_active?: boolean
} = {}): Promise<MusicChart[]> {
  const response = await api.get('/music/charts', { params })
  return response.data.items || response.data
}

export async function fetchMusicChartSources(): Promise<MusicChartSource[]> {
  const response = await api.get('/music/chart-sources')
  return response.data.items || response.data
}

// 音乐下载任务相关接口
export interface MusicDownloadJob {
  id: number
  subscription_id?: number | null
  chart_item_id?: number | null
  user_id: number
  search_query: string
  source_type: 'chart' | 'keyword'
  status: 'pending' | 'searching' | 'found' | 'downloading' | 'completed' | 'failed'
  torrent_title?: string | null
  torrent_url?: string | null
  torrent_size?: number | null
  torrent_info_hash?: string | null
  seeders?: number | null
  leechers?: number | null
  quality?: string | null
  format?: string | null
  site_name?: string | null
  downloader_hash?: string | null
  file_path?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
}

export async function fetchMusicDownloadJobs(params: {
  subscription_id?: number
  status?: string
  source_type?: 'chart' | 'keyword'
  page?: number
  page_size?: number
} = {}): Promise<{
  items: MusicDownloadJob[]
  total: number
  page: number
  page_size: number
  total_pages: number
}> {
  const response = await api.get('/music/download-jobs', { params })
  return response.data
}

// 音乐订阅运行相关接口
export interface MusicSubscriptionRunResult {
  subscription_id: number
  found_total: number
  filtered_out: Record<string, number>
  skipped_existing: number
  created_tasks: number
  errors: string[]
}

export interface MusicSubscriptionBatchRunResult {
  total_subscriptions: number
  runs: MusicSubscriptionRunResult[]
  summary: {
    found_total: number
    filtered_total: Record<string, number>
    created_tasks_total: number
    succeeded_checks: number
    failed_checks: number
  }
}

export async function runSubscriptionOnce(id: number, dryRun: boolean = false): Promise<MusicSubscriptionRunResult> {
  const response = await api.post(`/music/subscriptions/${id}/run_once`, null, {
    params: { dry_run: dryRun }
  })
  return response.data
}

export async function runAllSubscriptions(
  onlyActive: boolean = true,
  limit: number = 20,
  dryRun: boolean = false
): Promise<MusicSubscriptionBatchRunResult> {
  const response = await api.post('/music/subscriptions/run_all', null, {
    params: {
      only_active: onlyActive,
      limit: limit,
      dry_run: dryRun
    }
  })
  return response.data
}

