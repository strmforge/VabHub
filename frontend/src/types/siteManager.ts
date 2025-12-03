/**
 * 站点管理模块类型定义 (SITE-MANAGER-1)
 * 与后端Pydantic Schema对应的TypeScript类型
 */

// 站点分类枚举
export enum SiteCategory {
  PT = 'pt',
  BT = 'bt',
  NOVEL = 'novel',
  COMIC = 'comic',
  MUSIC = 'music',
  MOVIE = 'movie',
  GAME = 'game'
}

// 健康状态枚举
export enum HealthStatus {
  OK = 'OK',
  WARN = 'WARN',
  ERROR = 'ERROR',
  UNKNOWN = 'UNKNOWN'
}

// 检查类型枚举
export enum CheckType {
  BASIC = 'basic',
  RSS = 'rss',
  API = 'api'
}

// 站点分类模型
export interface SiteCategoryModel {
  id: number
  key: string
  name: string
  description?: string
  icon?: string
  sort_order: number
  enabled: boolean
  created_at: string
}

// 站点统计模型
export interface SiteStatsModel {
  id: number
  site_id: number
  upload_bytes: number
  download_bytes: number
  ratio?: number
  last_seen_at?: string
  last_error_at?: string
  error_count: number
  health_status: HealthStatus
  total_requests: number
  successful_requests: number
  avg_response_time?: number
  created_at: string
  updated_at: string
}

// 站点访问配置模型
export interface SiteAccessConfigModel {
  id: number
  site_id: number
  rss_url?: string
  api_key?: string
  auth_header?: string
  cookie?: string
  user_agent?: string
  use_api_mode: boolean
  use_proxy: boolean
  use_browser_emulation: boolean
  min_interval_seconds: number
  max_concurrent_requests: number
  timeout_seconds: number
  retry_count: number
  custom_headers?: string
  created_at: string
  updated_at: string
}

// 站点健康检查模型
export interface SiteHealthCheckModel {
  id: number
  site_id: number
  status: HealthStatus
  response_time_ms?: number
  error_message?: string
  http_status_code?: number
  check_type: CheckType
  checked_at: string
}

// 站点简要信息
export interface SiteBrief {
  id: number
  key?: string
  name: string
  domain?: string
  url: string
  category?: string
  icon_url?: string
  enabled: boolean
  priority: number
  tags?: string | string[]
  created_at: string
  updated_at: string
  stats?: SiteStatsModel
  access_config?: SiteAccessConfigModel
}

// 站点详细信息
export interface SiteDetail extends SiteBrief {
  stats?: SiteStatsModel
  access_config?: SiteAccessConfigModel
  recent_health_checks?: SiteHealthCheckModel[]
}

// 站点更新载荷
export interface SiteUpdatePayload {
  key?: string
  name?: string
  domain?: string
  url?: string
  category?: string
  icon_url?: string
  enabled?: boolean
  priority?: number
  tags?: string | string[]
}

// 站点访问配置载荷
export interface SiteAccessConfigPayload {
  rss_url?: string
  api_key?: string
  auth_header?: string
  cookie?: string
  user_agent?: string
  use_api_mode?: boolean
  use_proxy?: boolean
  use_browser_emulation?: boolean
  min_interval_seconds?: number
  max_concurrent_requests?: number
  timeout_seconds?: number
  retry_count?: number
  custom_headers?: string
}

// 站点列表过滤器
export interface SiteListFilter {
  enabled?: boolean | null
  category?: string | null
  health_status?: HealthStatus | null
  keyword?: string
  tags?: string[]
  priority_min?: number | null
  priority_max?: number | null
}

// 站点健康检查结果
export interface SiteHealthResult {
  site_id: number
  status: HealthStatus
  response_time_ms?: number
  error_message?: string
  http_status_code?: number
  check_type: CheckType
  checked_at: string
}

// 批量健康检查结果
export interface BatchHealthCheckResult {
  total: number
  success_count: number
  failed_count: number
  results: SiteHealthResult[]
  message: string
}

// 站点导入项
export interface SiteImportItem {
  key?: string
  name: string
  domain?: string
  url: string
  category?: string
  icon_url?: string
  enabled?: boolean
  priority?: number
  tags?: string | string[]
  rss_url?: string
  use_proxy?: boolean
  use_browser_emulation?: boolean
  min_interval_seconds?: number
  max_concurrent_requests?: number
}

// 站点导出项
export interface SiteExportItem {
  key?: string
  name: string
  domain?: string
  url: string
  category?: string
  icon_url?: string
  enabled: boolean
  priority: number
  tags?: string | string[]
  rss_url?: string
  use_proxy: boolean
  use_browser_emulation: boolean
  min_interval_seconds: number
  max_concurrent_requests: number
}

// 导入结果
export interface ImportResult {
  total: number
  success_count: number
  failed_count: number
  failed_items: Array<{
    site: SiteImportItem
    error: string
  }>
  message: string
}

// 站点统计摘要
export interface SiteStatsSummary {
  total_sites: number
  enabled_sites: number
  disabled_sites: number
  health_stats: Record<string, number>
  category_stats: Record<string, number>
}

// 站点卡片显示配置
export interface SiteCardConfig {
  showStats: boolean
  showHealth: boolean
  showPriority: boolean
  showTags: boolean
  compact: boolean
}

// 站点管理视图配置
export interface SiteManagerViewConfig {
  layout: 'grid' | 'list'
  cardSize: 'small' | 'medium' | 'large'
  sortBy: 'priority' | 'name' | 'created_at' | 'health_status'
  sortOrder: 'asc' | 'desc'
  showDisabled: boolean
  autoRefresh: boolean
  refreshInterval: number // 秒
  virtualScroll: boolean
  lazyLoadImages: boolean
  pageSize: number
}

// 站点操作类型
export enum SiteActionType {
  TOGGLE_ENABLED = 'toggle_enabled',
  ADJUST_PRIORITY = 'adjust_priority',
  HEALTH_CHECK = 'health_check',
  EDIT = 'edit',
  DELETE = 'delete',
  EXPORT = 'export',
  BATCH_HEALTH_CHECK = 'batch_health_check'
}

// 站点操作载荷
export interface SiteActionPayload {
  type: SiteActionType
  siteId?: number
  siteIds?: number[]
  data?: any
}

// 站点管理事件
export interface SiteManagerEvent {
  type: 'site_updated' | 'site_deleted' | 'health_checked' | 'filter_changed'
  data: any
  timestamp: string
}
